import sys
from pathlib import Path
import torch

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

# Force single thread
torch.set_num_threads(1)

from tts.tts_indic_parler import generate_speech_stream

text = "नमस्ते, मैं आपका रियल एस्टेट सलाहकार हूँ। मैं आपकी कैसे मदद कर सकता हूँ?"
description = "A young boy with a clear, calm, and moderate-paced voice speaking in Hindi."

print("Generating speech stream...")
try:
    chunks = []
    # Fetch first few chunks to verify generation works without waiting for full generation
    for i, chunk in enumerate(generate_speech_stream(text, preferred_language="hi", description=description)):
        chunks.append(chunk)
        if i == 5:
            print("First few audio chunks generated successfully!")
            break
    print("Successfully verified speech stream generation!")
except Exception as e:
    import traceback
    traceback.print_exc()
