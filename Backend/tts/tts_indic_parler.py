"""
AI4Bharat Indic Parler TTS adapter.

Uses the AI4Bharat Indic Parler-TTS model (parler-tts/indic-parler-tts)
via the Hugging Face transformers / parler_tts library to synthesize
high-quality Indian-language speech locally.

Preserves the existing TTS engine contract:
    generate_speech_stream(text, preferred_language) -> Iterator[bytes]

Yields raw PCM16 mono chunks at 24kHz — same as edge and cartesia providers.

Install dependencies:
    pip install parler-tts transformers accelerate soundfile scipy
    # or: pip install git+https://github.com/huggingface/parler-tts.git

Model used: ai4bharat/indic-parler-tts
    - Supports: Hindi, Marathi, Bengali, Tamil, Telugu, Kannada, Gujarati,
                Malayalam, Punjabi, Odia, Assamese, and English (Indian accent)
    - License: MIT
    - Offline / no API key required once model is cached locally
"""

from __future__ import annotations

import io
import logging
import os
import queue
import threading
import time
from collections import deque
from typing import Iterator

import numpy as np

from metrics.provider_metrics import record_provider_metric

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────
SAMPLE_RATE = 24000          # output Hz — matches rest of pipeline
_FADE_SAMPLES = int(SAMPLE_RATE * 0.05)   # 50 ms fade for pop-free audio
_SENTINEL = object()
_CHUNK_SIZE = 4096           # bytes per yielded PCM chunk

# Model identifier (can be overridden via env var)
_MODEL_ID = os.getenv(
    "INDIC_PARLER_MODEL_ID",
    "ai4bharat/indic-parler-tts"
)

# ── Language → voice description mapping ──────────────────────────────────
# Indic Parler uses natural-language prompts to control speaker identity.
# These prompts select a warm, female Indian voice appropriate for each
# language. Adjust the descriptions to change speaker characteristics.
_VOICE_DESCRIPTIONS: dict[str, str] = {
    "en": (
        "Neha speaks in a warm, clear Indian English accent with a moderate pace. "
        "Her voice is expressive and professional, with a friendly tone."
    ),
    "hi": (
        "Neha speaks in natural Hindi with a clear, warm female voice at a moderate pace. "
        "Her tone is friendly and professional."
    ),
    "hinglish": (
        "Neha speaks in conversational Hinglish, mixing Hindi and English naturally. "
        "Her voice is warm, expressive, and easy to understand."
    ),
    "mr": (
        "Neha speaks in fluent Marathi with a clear, warm female voice. "
        "Her tone is friendly and professional with a natural Maharashtrian accent."
    ),
    "bn": (
        "Neha speaks in natural Bengali with a warm, clear female voice."
    ),
    "ta": (
        "Neha speaks in Tamil with a natural, warm female voice."
    ),
    "te": (
        "Neha speaks in Telugu with a warm, natural female voice."
    ),
    "kn": (
        "Neha speaks in Kannada with a clear, warm female voice."
    ),
}

_DEFAULT_DESCRIPTION = _VOICE_DESCRIPTIONS["en"]

# ── Rolling latency tracking ───────────────────────────────────────────────
_ttfb_samples: deque = deque(maxlen=200)
_total_samples: deque = deque(maxlen=200)


def _percentile(values, p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * p))
    return ordered[idx]


# ── Lazy model loader (singleton per process) ──────────────────────────────
_model = None
_tokenizer = None
_model_lock = threading.Lock()


def _load_model():
    """Load Indic Parler model once and cache for reuse."""
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    with _model_lock:
        if _model is not None:          # double-check inside lock
            return _model, _tokenizer

        try:
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "Indic Parler TTS dependencies not installed. "
                "Run: pip install parler-tts transformers accelerate"
            ) from exc

        logger.info("[INDIC_PARLER] Loading model %s …", _MODEL_ID)
        t0 = time.perf_counter()

        device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
        dtype = __import__("torch").float16 if device == "cuda" else __import__("torch").bfloat16

        # Determine if we can load from a local cache snapshot directly to bypass gated repo auth
        from pathlib import Path
        model_path = _MODEL_ID
        backend_dir = Path(__file__).resolve().parents[1]
        cache_dir = backend_dir / ".hf_cache" / "hub" / "models--ai4bharat--indic-parler-tts" / "snapshots"
        if cache_dir.exists():
            snapshots = [d for d in cache_dir.iterdir() if d.is_dir()]
            if snapshots:
                model_path = str(snapshots[0])
                logger.info("[INDIC_PARLER] Found local cache snapshot. Loading from disk: %s", model_path)

        # Set default dtype to bfloat16 on CPU to avoid peak float32 allocation OOM
        if device == "cpu":
            __import__("torch").set_default_dtype(__import__("torch").bfloat16)

        model = ParlerTTSForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        ).to(device)

        # Restore default dtype to float32
        if device == "cpu":
            __import__("torch").set_default_dtype(__import__("torch").float32)
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        _model = model
        _tokenizer = tokenizer

        elapsed = time.perf_counter() - t0
        logger.info(
            "[INDIC_PARLER] Model loaded in %.1f s on %s (dtype=%s)",
            elapsed, device, dtype,
        )
    return _model, _tokenizer


# ── Text helpers ───────────────────────────────────────────────────────────

def _optimize_text(text: str) -> str:
    try:
        from tts.speech_formatter import optimize_for_tts
        return optimize_for_tts(text)
    except Exception:
        logger.debug("speech_formatter unavailable, using raw text")
        return text


def _voice_description(preferred_language: str | None) -> str:
    lang = (preferred_language or "en").lower()
    return _VOICE_DESCRIPTIONS.get(lang, _DEFAULT_DESCRIPTION)


# ── Fade helpers ───────────────────────────────────────────────────────────

def _apply_fades(pcm16: np.ndarray) -> np.ndarray:
    """Apply a 50 ms fade-in and fade-out to prevent audio pops."""
    n = len(pcm16)
    fc = min(_FADE_SAMPLES, n // 2)
    if fc <= 0:
        return pcm16
    data = pcm16.astype(np.float32)
    data[:fc] *= np.linspace(0.0, 1.0, fc)
    data[-fc:] *= np.linspace(1.0, 0.0, fc)
    return np.clip(data, -32768, 32767).astype(np.int16)


# ── Core synthesis (runs in background thread) ─────────────────────────────

def _synthesize(
    text: str,
    preferred_language: str | None,
    output_queue: "queue.Queue[object]",
    custom_description: str | None = None,
) -> None:
    """Generate speech and push raw PCM16 bytes into output_queue."""
    try:
        import torch

        model, tokenizer = _load_model()
        if custom_description and custom_description.strip():
            description = custom_description.strip()
        else:
            description = _voice_description(preferred_language)

        # Tokenize description + prompt text
        description_ids = tokenizer(description, return_tensors="pt").input_ids.to(model.device)
        prompt_ids = tokenizer(text, return_tensors="pt").input_ids.to(model.device)

        logger.info(
            "[INDIC_PARLER] Synthesizing %d chars | lang=%s",
            len(text), preferred_language or "en",
        )
        t0 = time.perf_counter()

        with torch.no_grad():
            generation = model.generate(
                input_ids=description_ids,
                prompt_input_ids=prompt_ids,
            )

        # generation shape: (1, T) — float waveform in model's native sample rate
        audio_arr = generation.cpu().squeeze().float().numpy()
        model_sr = model.config.sampling_rate

        logger.info(
            "[INDIC_PARLER] Raw audio: %.2f s at %d Hz (%.1f s inference)",
            len(audio_arr) / model_sr,
            model_sr,
            time.perf_counter() - t0,
        )

        # Resample to 24 kHz if the model uses a different sample rate
        if model_sr != SAMPLE_RATE:
            from scipy.signal import resample_poly
            import math
            g = math.gcd(SAMPLE_RATE, model_sr)
            audio_arr = resample_poly(audio_arr, SAMPLE_RATE // g, model_sr // g)

        # Convert float → PCM16
        pcm16 = _apply_fades((audio_arr * 32767).astype(np.int16))
        raw = pcm16.tobytes()

        # Push in streaming chunks
        for i in range(0, len(raw), _CHUNK_SIZE):
            output_queue.put(raw[i : i + _CHUNK_SIZE])

    except Exception as exc:
        logger.exception("[INDIC_PARLER] Synthesis failed: %s", exc)
    finally:
        output_queue.put(_SENTINEL)


# ── Public interface ───────────────────────────────────────────────────────

def generate_speech_stream(
    text: str,
    preferred_language: str | None = None,
    description: str | None = None,
) -> Iterator[bytes]:
    """
    Yield PCM16 mono 24kHz audio chunks using AI4Bharat Indic Parler TTS.

    Contract: same as tts_edge.py and tts_cartesia.py
    """
    if not text or not text.strip():
        yield b""
        return

    text = _optimize_text(text)

    out_q: "queue.Queue[object]" = queue.Queue(maxsize=128)
    producer = threading.Thread(
        target=_synthesize,
        args=(text, preferred_language, out_q, description),
        daemon=True,
    )

    started_at = time.perf_counter()
    first_chunk_at: float | None = None
    chunk_count = 0
    bytes_out = 0

    producer.start()

    while True:
        item = out_q.get()
        if item is _SENTINEL:
            break
        if not isinstance(item, (bytes, bytearray)) or not item:
            continue

        if first_chunk_at is None:
            first_chunk_at = time.perf_counter()
        chunk_count += 1
        bytes_out += len(item)
        yield bytes(item)

    # ── Metrics ────────────────────────────────────────────────────────────
    total_s = time.perf_counter() - started_at
    ttfb_s = (first_chunk_at - started_at) if first_chunk_at is not None else total_s
    _ttfb_samples.append(ttfb_s)
    _total_samples.append(total_s)

    logger.info(
        "[TTS METRICS] provider=indic_parler "
        "ttfb_ms=%.1f total_ms=%.1f "
        "p50_ms=%.1f p95_ms=%.1f "
        "chunks=%d bytes=%d",
        ttfb_s * 1000.0,
        total_s * 1000.0,
        _percentile(_total_samples, 0.50) * 1000.0,
        _percentile(_total_samples, 0.95) * 1000.0,
        chunk_count,
        bytes_out,
    )
    record_provider_metric("tts_ttfb", "indic_parler", ttfb_s * 1000.0)
    record_provider_metric("tts_total", "indic_parler", total_s * 1000.0)