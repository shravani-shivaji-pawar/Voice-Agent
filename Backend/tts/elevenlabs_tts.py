"""ElevenLabs TTS provider adapter.

Preserves the existing TTS engine contract:
    generate_speech_stream(text, preferred_language, ...) -> Iterator[bytes]

Yields raw PCM16 mono chunks at 24kHz.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add S:\lib to path to resolve ElevenLabs package on Windows systems with long path constraints
for p in ["s:\\lib", "S:\\lib"]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

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

SAMPLE_RATE = 24000
_FADE_SAMPLES = int(SAMPLE_RATE * 0.05)   # 50 ms fade to prevent audio pops
_SENTINEL = object()
_CHUNK_SIZE = 4096

_ttfb_samples: deque = deque(maxlen=200)
_total_samples: deque = deque(maxlen=200)


def _percentile(values, p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * p))
    return ordered[idx]


def _optimize_text(text: str) -> str:
    try:
        from tts.speech_formatter import optimize_for_tts
        return optimize_for_tts(text)
    except Exception:
        logger.debug("speech_formatter unavailable, using raw text")
        return text


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


def _synthesize(
    text: str,
    output_queue: queue.Queue,
    voice_id: str | None = None,
    model: str | None = None,
    stability: float | None = None,
    similarity: float | None = None,
    style: float | None = None,
    speaker_boost: bool | None = None,
) -> None:
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import VoiceSettings
        
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not configured.")

        client = ElevenLabs(api_key=api_key)

        # Default fallback configurations
        selected_voice_id = (voice_id or "EXAVITQu4vr4xnSDxMaL").strip()  # Sarah default (free tier compatible)
        selected_model = (model or "eleven_flash_v2_5").strip()

        # Handle voice settings
        stability_val = 0.5 if stability is None else stability
        similarity_val = 0.75 if similarity is None else similarity
        style_val = 0.0 if style is None else style
        speaker_boost_val = True if speaker_boost is None else speaker_boost

        logger.info(
            "[ELEVENLABS] Synthesizing: model=%s voice=%s stability=%.2f similarity=%.2f style=%.2f speaker_boost=%s",
            selected_model, selected_voice_id, stability_val, similarity_val, style_val, speaker_boost_val
        )

        settings = VoiceSettings(
            stability=stability_val,
            similarity_boost=similarity_val,
            style=style_val,
            use_speaker_boost=speaker_boost_val
        )

        # Request PCM mono at 24kHz stream
        audio_stream = client.text_to_speech.convert(
            voice_id=selected_voice_id,
            text=text,
            model_id=selected_model,
            output_format="pcm_24000",
            voice_settings=settings
        )

        for chunk in audio_stream:
            if chunk:
                output_queue.put(chunk)
                
    except Exception as exc:
        error_msg = str(exc)
        is_library_restriction = (
            "paid_plan_required" in error_msg or
            "Free users cannot use library voices" in error_msg or
            (hasattr(exc, "status_code") and exc.status_code == 402)
        )
        if is_library_restriction:
            logger.error(
                "\n" + "=" * 80 + "\n"
                "❌ ELEVENLABS FREE-TIER LIMITATION DETECTED:\n"
                "You are attempting to use a shared Voice Library voice directly via API on a FREE account.\n"
                "ElevenLabs restricts direct API usage of public library voices to paid subscriptions.\n\n"
                "HOW TO FIX THIS:\n"
                "1. Go to the ElevenLabs website and find the desired voice in the Voice Library.\n"
                "2. Click 'Add to Voice Lab' to clone it into your account.\n"
                "3. Copy the NEW Voice ID generated in your Voice Lab dashboard.\n"
                "4. Paste this NEW Voice ID into your Agent's custom voice settings.\n"
                "This allows ElevenLabs to synthesize the voice for free as a custom Voice Lab voice.\n" +
                "=" * 80 + "\n"
            )
        else:
            logger.exception("[ELEVENLABS] Synthesis execution failed: %s", exc)
        output_queue.put(exc)
    finally:
        output_queue.put(_SENTINEL)


def generate_speech_stream(
    text: str,
    preferred_language: str | None = None,
    voice_id: str | None = None,
    model: str | None = None,
    stability: float | None = None,
    similarity: float | None = None,
    style: float | None = None,
    speaker_boost: bool | None = None,
) -> Iterator[bytes]:
    """Yield PCM16 mono 24kHz audio chunks using ElevenLabs TTS."""
    if not text or not text.strip():
        yield b""
        return

    text = _optimize_text(text)

    # Output queue for consumer thread
    out_q: queue.Queue = queue.Queue(maxsize=128)
    producer = threading.Thread(
        target=_synthesize,
        args=(text, out_q, voice_id, model, stability, similarity, style, speaker_boost),
        daemon=True,
    )

    started_at = time.perf_counter()
    first_chunk_at: float | None = None
    chunk_count = 0
    bytes_out = 0
    faded_samples = 0
    previous_chunk = None

    producer.start()

    while True:
        item = out_q.get()
        if item is _SENTINEL:
            break
        if isinstance(item, Exception):
            # Propagate synthesis errors so caller can handle fallback
            raise item
        if not isinstance(item, (bytes, bytearray)) or not item:
            continue

        chunk, faded_samples = _apply_fade_in(bytes(item), faded_samples)
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
    _ttfb_samples.append(ttfb_s)
    _total_samples.append(total_s)

    logger.info(
        "[TTS METRICS] provider=elevenlabs ttfb_ms=%.1f total_ms=%.1f chunks=%d bytes=%d",
        ttfb_s * 1000.0,
        total_s * 1000.0,
        chunk_count,
        bytes_out,
    )
    record_provider_metric("tts_ttfb", "elevenlabs", ttfb_s * 1000.0)
    record_provider_metric("tts_total", "elevenlabs", total_s * 1000.0)
