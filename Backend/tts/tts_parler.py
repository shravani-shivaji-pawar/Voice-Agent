"""AI4Bharat Indic Parler TTS adapter.

This adapter preserves the existing TTS engine contract:
    generate_speech_stream(text, preferred_language, description) -> Iterator[bytes]

It supports both a remote streaming HTTP API (via httpx) and a local lazy-loaded model.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Iterator
import httpx
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000
_FADE_SAMPLES = int(SAMPLE_RATE * 0.05)

# Default voice/style descriptions per language
_DEFAULT_DESCRIPTIONS = {
    "hi": "A female speaker with a clear, calm, and moderate-paced voice speaking in Hindi with natural delivery.",
    "mr": "A female speaker with a clear, calm, and moderate-paced voice speaking in Marathi with good intonation.",
    "en": "A female speaker with a clear, calm, and moderate-paced voice speaking in English."
}

def _description_for(preferred_language: str | None, custom_description: str | None = None) -> str:
    if custom_description and custom_description.strip():
        return custom_description.strip()
    
    lang = (preferred_language or "en").strip().lower()
    if lang in ("hi", "hinglish"):
        return _DEFAULT_DESCRIPTIONS["hi"]
    elif lang == "mr":
        return _DEFAULT_DESCRIPTIONS["mr"]
    return _DEFAULT_DESCRIPTIONS["en"]

# Local generation cache
_model = None
_tokenizer = None
_device = None

def _get_local_model_and_tokenizer():
    global _model, _tokenizer, _device
    if _model is not None:
        return _model, _tokenizer, _device
    
    import torch  # type: ignore
    from transformers import AutoTokenizer  # type: ignore
    from parler_tts import ParlerTTSForConditionalGeneration  # type: ignore
    
    model_id = os.getenv("PARLER_MODEL_ID", "ai4bharat/indic-parler-tts-mini")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"[Parler TTS] Loading local model {model_id} on device {device}...")
    
    _tokenizer = AutoTokenizer.from_pretrained(model_id)
    _model = ParlerTTSForConditionalGeneration.from_pretrained(model_id).to(device)
    _device = device
    logger.info("[Parler TTS] Local model loaded successfully.")
    return _model, _tokenizer, _device

def _generate_local(text: str, description: str) -> Iterator[bytes]:
    import torch  # type: ignore
    model, tokenizer, device = _get_local_model_and_tokenizer()
    
    input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
    prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)
    
    try:
        from parler_tts import ParlerTTSStreamer  # type: ignore
        streamer = ParlerTTSStreamer(model, device=device)
        generation_kwargs = dict(
            input_ids=input_ids,
            prompt_input_ids=prompt_input_ids,
            streamer=streamer,
            max_new_tokens=1024,
        )
        
        import threading
        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        for new_audio in streamer:
            if new_audio is not None and len(new_audio) > 0:
                pcm16 = (new_audio * 32767).astype(np.int16)
                yield pcm16.tobytes()
        thread.join()
    except Exception as e:
        logger.warning(f"[Parler TTS] Streamer failed or not available, falling back to full generation: {e}")
        with torch.no_grad():
            generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation[0].cpu().numpy()
            pcm16 = (audio_arr * 32767).astype(np.int16)
            yield pcm16.tobytes()

def _apply_fade_in(chunk: bytes, faded_samples: int) -> tuple[bytes, int]:
    if not chunk or faded_samples >= _FADE_SAMPLES:
        return chunk, faded_samples
    if len(chunk) % 2:
        chunk = chunk[:-1]
    samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
    fade_count = min(len(samples), _FADE_SAMPLES - faded_samples)
    if fade_count <= 0:
        return chunk, faded_samples
    start = faded_samples / float(_FADE_SAMPLES)
    stop = (faded_samples + fade_count) / float(_FADE_SAMPLES)
    samples[:fade_count] *= np.linspace(start, stop, fade_count, endpoint=False)
    return np.clip(samples, -32768, 32767).astype(np.int16).tobytes(), faded_samples + fade_count

def _apply_fade_out(chunk: bytes) -> bytes:
    if not chunk:
        return chunk
    if len(chunk) % 2:
        chunk = chunk[:-1]
    samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
    fade_count = min(len(samples), _FADE_SAMPLES)
    if fade_count <= 0:
        return chunk
    samples[-fade_count:] *= np.linspace(1.0, 0.0, fade_count)
    return np.clip(samples, -32768, 32767).astype(np.int16).tobytes()

def generate_speech_stream(
    text: str,
    preferred_language: str | None = None,
    description: str | None = None,
) -> Iterator[bytes]:
    """Yield PCM16 mono chunks from Parler-TTS (API or Local mode)."""
    if not text or not text.strip():
        yield b""
        return

    resolved_description = _description_for(preferred_language, description)
    local_mode = os.getenv("PARLER_LOCAL", "false").strip().lower() in ("1", "true", "yes", "on")

    started_at = time.perf_counter()
    first_chunk_at = None
    chunk_count = 0
    bytes_out = 0
    faded_samples = 0
    previous_chunk = None

    def raw_chunks_generator() -> Iterator[bytes]:
        if local_mode:
            logger.info(f"[Parler TTS] Running local generation for: '{text[:30]}...'")
            yield from _generate_local(text, resolved_description)
        else:
            api_url = os.getenv("PARLER_API_URL", "http://127.0.0.1:8001/tts").strip()
            logger.info(f"[Parler TTS] Querying API {api_url} for description: '{resolved_description}'")
            try:
                timeout = httpx.Timeout(2.0, connect=0.1)
                with httpx.stream("POST", api_url, json={"text": text, "description": resolved_description}, timeout=timeout) as response:
                    if response.status_code == 200:
                        for chunk in response.iter_bytes():
                            if chunk:
                                yield chunk
                    else:
                        logger.error(f"[Parler TTS] API returned status code {response.status_code}")
            except Exception as e:
                logger.exception(f"[Parler TTS] Remote API streaming failed: {e}")

    for item in raw_chunks_generator():
        if not item:
            continue
        chunk, faded_samples = _apply_fade_in(item, faded_samples)
        if previous_chunk is not None:
            if first_chunk_at is None:
                first_chunk_at = time.perf_counter()
            chunk_count += 1
            bytes_out += len(previous_chunk)
            yield previous_chunk
        previous_chunk = chunk

    if previous_chunk:
        final_chunk = _apply_fade_out(previous_chunk)
        if first_chunk_at is None:
            first_chunk_at = time.perf_counter()
        chunk_count += 1
        bytes_out += len(final_chunk)
        yield final_chunk

    total_s = time.perf_counter() - started_at
    ttfb_s = (first_chunk_at - started_at) if first_chunk_at is not None else total_s
    logger.info(
        "[TTS METRICS] provider=parler ttfb_ms=%.1f total_ms=%.1f chunks=%d bytes=%d",
        ttfb_s * 1000.0,
        total_s * 1000.0,
        chunk_count,
        bytes_out,
    )
    
    try:
        from metrics.provider_metrics import record_provider_metric
        record_provider_metric("tts_ttfb", "parler", ttfb_s * 1000.0)
        record_provider_metric("tts_total", "parler", total_s * 1000.0)
    except Exception:
        pass
