import sys
from pathlib import Path

# Add Backend to python path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

import traceback
import os
os.environ["INDIC_PARLER_MODEL_ID"] = "ai4bharat/indic-parler-tts"
try:
    from tts import tts_indic_parler
    print("Attempting to load model...")
    tts_indic_parler._load_model()
    print("Successfully loaded model!")
except Exception as e:
    print("Error loading model:", e)
    traceback.print_exc()


