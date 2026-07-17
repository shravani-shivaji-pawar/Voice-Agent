"""
test_elevenlabs_agent.py
========================
End-to-end test for the Priya/ElevenLabs agent that uses ElevenLabs TTS.

Three test modes
----------------
1. TTS UNIT TEST  (--mode tts)
   Synthesises a few sample sentences in different languages and plays them
   through the speaker so you can hear the ElevenLabs voice quality.
   No microphone required.

2. CONVERSATION DEMO  (--mode demo)  [DEFAULT]
   Runs a full demo conversation using simulated human responses (same
   DemoCallEngine used in production). Prints the transcript but does NOT
   play audio — suitable for headless / CI environments.

3. LIVE MIC TEST  (--mode mic)
   Runs the complete real-time pipeline:
     Microphone → Deepgram/Groq STT → Groq LLM → ElevenLabs TTS → Speaker
   Requires a working microphone, speaker, and valid .env keys.

Usage
-----
    cd Backend
    python db/agents/test_elevenlabs_agent.py                    # demo mode
    python db/agents/test_elevenlabs_agent.py --mode tts         # TTS unit test
    python db/agents/test_elevenlabs_agent.py --mode mic         # live mic test
    python db/agents/test_elevenlabs_agent.py --mode demo --turns 5

Prerequisites
-------------
    # Ensure your .env has ELEVENLABS_API_KEY and GROQ_API_KEY
"""

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
import sys
import time
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

# Ensure ElevenLabs custom module path is resolved
for p in ["s:\\lib", "S:\\lib"]:
    if Path(p).exists() and p not in sys.path:
        sys.path.insert(0, p)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("test_elevenlabs_agent")

# ── Agent configuration ────────────────────────────────────────────────────
AGENT_JSON_PATH = str(_BACKEND / "db" / "agents" / "elevenlabs_agent.json")

# Force ElevenLabs as TTS provider for this test session
os.environ["TTS_PROVIDER"] = "elevenlabs"
os.environ["TTS_FALLBACK_ENABLED"] = "true"   # fall back to default if model unavailable


# ══════════════════════════════════════════════════════════════════════════
# MODE 1 — TTS UNIT TEST
# ══════════════════════════════════════════════════════════════════════════

TTS_SAMPLE_SENTENCES = [
    ("en",        "Hello! I am Priya from the Real Estate AI team. How are you doing today?"),
    ("hi",        "Namaste! Main Priya hoon, Real Estate AI team se. Kya aap property kharidne mein interested hain?"),
    ("hinglish",  "Bilkul! Hum aapko best properties Pune aur Mumbai mein suggest kar sakte hain within your budget."),
]


def _play_pcm16(pcm_bytes: bytes, sample_rate: int = 24000) -> None:
    """Play raw PCM16 bytes through the system speaker using sounddevice."""
    try:
        import sounddevice as sd
        import numpy as np

        arr = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sd.play(arr, samplerate=sample_rate)
        sd.wait()
    except Exception as exc:
        logger.warning("Speaker playback failed: %s", exc)


def run_tts_unit_test() -> None:
    """Synthesise sample sentences and play them back."""
    print("\n" + "=" * 60)
    print("  TTS UNIT TEST — ElevenLabs TTS")
    print("=" * 60)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("\n[ERROR] ELEVENLABS_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    try:
        from tts.elevenlabs_tts import generate_speech_stream
    except ImportError as exc:
        print(f"\n[ERROR] Import failed: {exc}")
        sys.exit(1)

    for lang, text in TTS_SAMPLE_SENTENCES:
        print(f"\n[{lang.upper()}] {text}")
        t0 = time.perf_counter()
        try:
            chunks = list(generate_speech_stream(
                text,
                preferred_language=lang,
                voice_id="EXAVITQu4vr4xnSDxMaL", # Sarah (premade, available on free tier)
                model="eleven_multilingual_v2"
            ))
            elapsed = time.perf_counter() - t0
            pcm_bytes = b"".join(chunks)
            print(f"  -> {len(pcm_bytes):,} bytes  |  {elapsed:.2f} s synthesis time")

            if pcm_bytes:
                print("  -> Playing...")
                _play_pcm16(pcm_bytes)
                time.sleep(0.4)           # brief pause between samples
            else:
                print("  [WARNING] No audio produced.")
        except Exception as e:
            print(f"  [ERROR] Synthesis failed: {e}")

    print("\n[SUCCESS] TTS unit test complete.\n")


# ══════════════════════════════════════════════════════════════════════════
# MODE 2 — CONVERSATION DEMO (no audio playback)
# ══════════════════════════════════════════════════════════════════════════

async def run_demo_conversation(max_turns: int = 8) -> None:
    """Run a simulated conversation through the full pipeline (no audio)."""
    print("\n" + "=" * 60)
    print("  CONVERSATION DEMO — Priya (ElevenLabs TTS)")
    print("=" * 60)

    try:
        from demo_runner import DemoCallEngine
    except ImportError as exc:
        print(f"\n[ERROR] Could not import DemoCallEngine: {exc}")
        sys.exit(1)

    engine = DemoCallEngine(ws_manager=None, db=None)

    lead = {
        "name": "Rahul Sharma",
        "phone": "+91 98200 11111",
    }

    print(f"\nLead     : {lead['name']} ({lead['phone']})")
    print(f"Agent    : Priya — ElevenLabs TTS")
    print(f"Schema   : {AGENT_JSON_PATH}")
    print(f"Max turns: {max_turns}\n")

    result = await engine.run_demo_call(
        campaign_id="test_elevenlabs_001",
        lead=lead,
        agent_schema_path=AGENT_JSON_PATH,
    )

    print("\n-- TRANSCRIPT ------------------------------------------")
    for turn in result.get("transcription", []):
        role  = turn.get("role", "?").upper()
        label = "  PRIYA " if role == "ASSISTANT" else "  USER  "
        print(f"{label}: {turn.get('content', '')}")

    print("\n-- COLLECTED DATA ---------------------------------------")
    lead_data = result.get("lead_data", {})
    for k, v in lead_data.items():
        if v:
            print(f"  {k:20s}: {v}")

    print(f"\n  Status      : {result.get('status')}")
    print(f"  Interested  : {result.get('interested')}")
    print(f"  Duration    : {result.get('duration')}")
    print("\n[SUCCESS] Demo conversation complete.\n")


# ══════════════════════════════════════════════════════════════════════════
# MODE 3 — LIVE MIC TEST
# ══════════════════════════════════════════════════════════════════════════

async def run_live_mic_test() -> None:
    """
    Runs the full real-time pipeline with ElevenLabs TTS.

    Microphone → STT → LLM (Priya persona) → ElevenLabs TTS → Speaker
    """
    print("\n" + "=" * 60)
    print("  LIVE MIC TEST — Priya (ElevenLabs TTS)")
    print("=" * 60)

    if not os.getenv("GROQ_API_KEY"):
        print("\n[ERROR] GROQ_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("\n[ERROR] ELEVENLABS_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    # Point StateManager at the ElevenLabs agent schema
    import flows.runtime as runtime_mod
    runtime_mod.STATE_SCHEMA_PATH = AGENT_JSON_PATH
    logger.info("StateManager will use schema: %s", AGENT_JSON_PATH)

    try:
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineTask
        from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams
        from flows.runtime import RealEstateSTTProcessor, RealEstateLLMProcessor, RealEstateTTSProcessor
    except ImportError as exc:
        print(f"\n[ERROR] Pipecat import failed: {exc}")
        print("    Install: pip install pipecat-ai sounddevice pyaudio")
        sys.exit(1)

    # Audio device info
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        print(f"  Microphone : {pa.get_default_input_device_info()['name']}")
        print(f"  Speaker    : {pa.get_default_output_device_info()['name']}")
        pa.terminate()
    except Exception:
        pass

    transport = LocalAudioTransport(LocalAudioTransportParams(
        audio_in_sample_rate=16000,
        audio_out_sample_rate=24000,
    ))

    turn_state_obj = None
    try:
        from flows.runtime import VoiceTurnState
        turn_state_obj = VoiceTurnState()
    except ImportError:
        pass

    stt = RealEstateSTTProcessor(turn_state=turn_state_obj)
    llm = RealEstateLLMProcessor(turn_state=turn_state_obj)
    # Pass agent_id so provider.py picks "elevenlabs" from the agent schema
    tts = RealEstateTTSProcessor(turn_state=turn_state_obj, agent_id="elevenlabs_agent")

    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        tts,
        transport.output(),
    ])

    runner = PipelineRunner()
    task = PipelineTask(pipeline)

    print("\n" + "=" * 60)
    print("  Pipeline running - speak into the microphone.")
    print("   Priya will respond using ElevenLabs TTS.")
    print("   Press Ctrl+C to stop.")
    print("=" * 60 + "\n")

    try:
        await runner.run(task)
    except KeyboardInterrupt:
        print("\n  Stopped by user.")
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)


# ══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test the Priya agent with ElevenLabs TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["tts", "demo", "mic"],
        default="demo",
        help="Test mode: tts (unit), demo (simulated call), mic (live) [default: demo]",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=8,
        help="Max conversation turns in demo mode [default: 8]",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.mode == "tts":
        run_tts_unit_test()
    elif args.mode == "demo":
        asyncio.run(run_demo_conversation(max_turns=args.turns))
    elif args.mode == "mic":
        asyncio.run(run_live_mic_test())
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
