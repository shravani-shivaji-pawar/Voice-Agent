"""TTS provider selection.

The runtime contract stays stable:
    generate_speech_stream(text: str, preferred_language: str | None) -> Iterator[bytes]

Providers must yield raw PCM16 mono chunks at 24kHz.
"""

from __future__ import annotations

import logging
import os
import json
import threading
import time
from pathlib import Path
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "indic_parler"
# ── NEW: indic_parler added to supported providers ─────────────────────────
SUPPORTED_PROVIDERS = {"edge", "cartesia", "indic_parler", "elevenlabs"}
_AGENT_CONFIG_CACHE: dict[str, tuple[float, dict]] = {}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_provider(provider: str | None) -> str:
    normalized = (provider or DEFAULT_PROVIDER).strip().lower()
    if normalized == "parler":
        normalized = "indic_parler"
    if normalized not in SUPPORTED_PROVIDERS:
        logger.warning("Unknown TTS_PROVIDER=%s; falling back to %s", provider, DEFAULT_PROVIDER)
        return DEFAULT_PROVIDER
    return normalized


def _configured_provider(agent_id: str = "default") -> str:
    global_provider = _normalize_provider(os.getenv("TTS_PROVIDER", DEFAULT_PROVIDER))
    if _env_bool("TTS_DISABLE_AGENT_OVERRIDES", False):
        return global_provider

    schema_config = _provider_config_from_agent_schema(agent_id)
    schema_provider = schema_config.get("tts_provider")
    if schema_provider:
        return schema_provider

    # Legacy env-var override for Cartesia
    cartesia_agent_ids = {
        item.strip()
        for item in os.getenv("CARTESIA_AGENT_IDS", "").split(",")
        if item.strip()
    }
    if agent_id and agent_id in cartesia_agent_ids:
        return "cartesia"

    # NEW: env-var override for Indic Parler
    indic_parler_agent_ids = {
        item.strip()
        for item in os.getenv("INDIC_PARLER_AGENT_IDS", "").split(",")
        if item.strip()
    }
    if agent_id and agent_id in indic_parler_agent_ids:
        return "indic_parler"

    return global_provider


def _provider_config_from_agent_schema(agent_id: str) -> dict:
    if not agent_id or agent_id == "default":
        return {}

    # Check cache (expire after 30 s)
    cached = _AGENT_CONFIG_CACHE.get(agent_id)
    if cached and (time.time() - cached[0]) < 30.0:
        return cached[1]

    config = {}
    try:
        url = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000") + f"/api/agents/{agent_id}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2.0) as response:
            if response.status == 200:
                schema = json.loads(response.read().decode())
                provider_config = schema.get("provider_config") or {}
                provider = provider_config.get("tts_provider") or schema.get("tts_provider")
                if provider:
                    config["tts_provider"] = _normalize_provider(provider)
                cartesia_voice_id = provider_config.get("cartesia_voice_id") or schema.get("cartesia_voice_id")
                if cartesia_voice_id:
                    config["cartesia_voice_id"] = str(cartesia_voice_id).strip()
                # NEW: indic_parler voice description override
                indic_voice_desc = (
                    provider_config.get("parler_description")
                    or schema.get("parler_description")
                    or provider_config.get("indic_parler_voice_description")
                    or schema.get("indic_parler_voice_description")
                )
                if indic_voice_desc:
                    config["indic_parler_voice_description"] = indic_voice_desc

                # ElevenLabs Config
                eleven_voice = provider_config.get("elevenlabs_voice_id") or schema.get("elevenlabs_voice_id")
                if eleven_voice:
                    config["elevenlabs_voice_id"] = str(eleven_voice).strip()
                eleven_model = provider_config.get("elevenlabs_model") or schema.get("elevenlabs_model")
                if eleven_model:
                    config["elevenlabs_model"] = str(eleven_model).strip()
                eleven_stability = provider_config.get("elevenlabs_stability") or schema.get("elevenlabs_stability")
                if eleven_stability is not None:
                    config["elevenlabs_stability"] = float(eleven_stability)
                eleven_similarity = provider_config.get("elevenlabs_similarity") or schema.get("elevenlabs_similarity")
                if eleven_similarity is not None:
                    config["elevenlabs_similarity"] = float(eleven_similarity)
                eleven_style = provider_config.get("elevenlabs_style") or schema.get("elevenlabs_style")
                if eleven_style is not None:
                    config["elevenlabs_style"] = float(eleven_style)
                eleven_speaker_boost = provider_config.get("elevenlabs_speaker_boost") or schema.get("elevenlabs_speaker_boost")
                if eleven_speaker_boost is not None:
                    config["elevenlabs_speaker_boost"] = bool(eleven_speaker_boost)
            else:
                raise RuntimeError(f"Backend API returned status {response.status}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            logger.info("Agent %s not found in API, falling back to default TTS provider.", agent_id)
            config = {}
        else:
            logger.error("API error for TTS provider config agent_id=%s: %s", agent_id, exc)
            raise RuntimeError(f"Backend API error ({exc.code}) while fetching TTS configuration.") from exc
    except urllib.error.URLError as exc:
        logger.error("Could not read TTS provider config for agent_id=%s from API: %s", agent_id, exc)
        raise RuntimeError("Backend API must be running to fetch TTS configuration.") from exc
    except Exception as exc:
        logger.error("Unexpected error fetching TTS config: %s", exc)
        raise RuntimeError("Unexpected error fetching TTS configuration from API.") from exc

    _AGENT_CONFIG_CACHE[agent_id] = (time.time(), config)
    return config


def _cartesia_voice_id_for_agent(agent_id: str) -> str | None:
    return _provider_config_from_agent_schema(agent_id).get("cartesia_voice_id")


def _shadow_provider(primary_provider: str) -> str:
    configured = os.getenv("TTS_SHADOW_PROVIDER")
    if configured:
        return _normalize_provider(configured)
    # Default shadow: if primary is edge → shadow with cartesia; otherwise → edge
    if primary_provider == "edge":
        return "cartesia"
    if primary_provider == "indic_parler":
        return "edge"
    return "edge"


def _load_provider(provider: str):
    if provider == "cartesia":
        from .tts_cartesia import generate_speech_stream as _cartesia
        return _cartesia
    if provider == "indic_parler":
        from .tts_indic_parler import generate_speech_stream as _indic_parler
        return _indic_parler
    if provider == "elevenlabs":
        from .elevenlabs_tts import generate_speech_stream as _elevenlabs
        return _elevenlabs
    from .tts_edge import generate_speech_stream as _edge
    return _edge


def _consume_shadow(provider: str, text: str, preferred_language: str | None) -> None:
    started_at = time.perf_counter()
    first_chunk_at = None
    chunks = 0
    bytes_out = 0
    try:
        for chunk in _load_provider(provider)(text, preferred_language):
            if not chunk:
                continue
            if first_chunk_at is None:
                first_chunk_at = time.perf_counter()
            chunks += 1
            bytes_out += len(chunk)
        total_s = time.perf_counter() - started_at
        ttfb_s = (first_chunk_at - started_at) if first_chunk_at is not None else total_s
        logger.info(
            "[TTS SHADOW] shadow_provider=%s ttfb_ms=%.1f total_ms=%.1f chunks=%d bytes=%d",
            provider,
            ttfb_s * 1000.0,
            total_s * 1000.0,
            chunks,
            bytes_out,
        )
    except Exception as exc:
        logger.warning("[TTS SHADOW] shadow_provider=%s failed without affecting live audio: %s", provider, exc)


def _stream_provider(
    provider: str,
    text: str,
    preferred_language: str | None,
    cartesia_voice_id: str | None = None,
    indic_parler_voice_description: str | None = None,
    elevenlabs_voice_id: str | None = None,
    elevenlabs_model: str | None = None,
    elevenlabs_stability: float | None = None,
    elevenlabs_similarity: float | None = None,
    elevenlabs_style: float | None = None,
    elevenlabs_speaker_boost: bool | None = None,
):
    if provider == "cartesia":
        return _load_provider(provider)(text, preferred_language, voice_id=cartesia_voice_id)
    if provider == "indic_parler":
        return _load_provider(provider)(text, preferred_language, description=indic_parler_voice_description)
    if provider == "elevenlabs":
        return _load_provider(provider)(
            text,
            preferred_language,
            voice_id=elevenlabs_voice_id,
            model=elevenlabs_model,
            stability=elevenlabs_stability,
            similarity=elevenlabs_similarity,
            style=elevenlabs_style,
            speaker_boost=elevenlabs_speaker_boost,
        )
    # edge and other share the same (text, preferred_language) signature
    return _load_provider(provider)(text, preferred_language)


def generate_speech_stream(
    text: str,
    preferred_language: str | None = None,
    agent_id: str = "default",
):
    """Yield live TTS audio from the selected provider."""
    primary_provider = _configured_provider(agent_id)
    cartesia_voice_id = _cartesia_voice_id_for_agent(agent_id)
    indic_voice_desc = _provider_config_from_agent_schema(agent_id).get("indic_parler_voice_description")

    if _env_bool("TTS_SHADOW_MODE", False):
        shadow = _shadow_provider(primary_provider)
        if shadow != primary_provider:
            threading.Thread(
                target=_consume_shadow,
                args=(shadow, text, preferred_language),
                daemon=True,
            ).start()

    agent_config = _provider_config_from_agent_schema(agent_id)
    elevenlabs_voice_id = agent_config.get("elevenlabs_voice_id")
    elevenlabs_model = agent_config.get("elevenlabs_model")
    elevenlabs_stability = agent_config.get("elevenlabs_stability")
    elevenlabs_similarity = agent_config.get("elevenlabs_similarity")
    elevenlabs_style = agent_config.get("elevenlabs_style")
    elevenlabs_speaker_boost = agent_config.get("elevenlabs_speaker_boost")

    nonempty_yielded = False
    try:
        for chunk in _stream_provider(
            primary_provider,
            text,
            preferred_language,
            cartesia_voice_id=cartesia_voice_id,
            indic_parler_voice_description=indic_voice_desc,
            elevenlabs_voice_id=elevenlabs_voice_id,
            elevenlabs_model=elevenlabs_model,
            elevenlabs_stability=elevenlabs_stability,
            elevenlabs_similarity=elevenlabs_similarity,
            elevenlabs_style=elevenlabs_style,
            elevenlabs_speaker_boost=elevenlabs_speaker_boost,
        ):
            if chunk:
                nonempty_yielded = True
            yield chunk
    except Exception as exc:
        logger.exception("[TTS PROVIDER] primary=%s failed: %s", primary_provider, exc)

    if (
        not nonempty_yielded
        and primary_provider != DEFAULT_PROVIDER
        and _env_bool("TTS_FALLBACK_ENABLED", True)
        and text
        and text.strip()
    ):
        logger.warning(
            "[TTS PROVIDER] primary=%s produced no audio; falling back to %s",
            primary_provider,
            DEFAULT_PROVIDER,
        )
        try:
            for chunk in _stream_provider(
                DEFAULT_PROVIDER,
                text,
                preferred_language,
                cartesia_voice_id=cartesia_voice_id,
                indic_parler_voice_description=indic_voice_desc,
                elevenlabs_voice_id=elevenlabs_voice_id,
                elevenlabs_model=elevenlabs_model,
                elevenlabs_stability=elevenlabs_stability,
                elevenlabs_similarity=elevenlabs_similarity,
                elevenlabs_style=elevenlabs_style,
                elevenlabs_speaker_boost=elevenlabs_speaker_boost,
            ):
                yield chunk
        except Exception as fallback_exc:
            logger.exception("[TTS PROVIDER] fallback=%s failed: %s", DEFAULT_PROVIDER, fallback_exc)
            yield b""