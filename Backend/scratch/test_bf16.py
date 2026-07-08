import sys
from pathlib import Path
import torch

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

model_id = "ai4bharat/indic-parler-tts"
cache_dir = "S:/voice agent/Voice_Agent/Backend/.hf_cache"

print("Loading model in bfloat16 on CPU...")
try:
    model = ParlerTTSForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        cache_dir=cache_dir
    )
    print("Model loaded successfully in bfloat16!")
    print("Memory used by model parameters:", sum(p.numel() * p.element_size() for p in model.parameters()) / (1024**2), "MB")
except Exception as e:
    import traceback
    traceback.print_exc()
