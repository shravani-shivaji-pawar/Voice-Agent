import sys
from pathlib import Path
import torch

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

# Force single thread to rule out OpenMP thread crashes
torch.set_num_threads(1)
print("Number of PyTorch CPU threads set to 1")

from parler_tts import ParlerTTSConfig, ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

model_id = "ai4bharat/indic-parler-tts"
cache_dir = "S:/voice agent/Voice_Agent/Backend/.hf_cache"

print("Loading configuration...")
config = ParlerTTSConfig.from_pretrained(model_id, cache_dir=cache_dir)
print("Configuration loaded successfully!")

print("Initializing model from configuration (no weights)...")
try:
    model = ParlerTTSForConditionalGeneration(config)
    print("Model initialized from configuration successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
