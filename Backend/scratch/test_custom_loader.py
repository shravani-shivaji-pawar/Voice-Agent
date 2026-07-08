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

from safetensors import safe_open
from parler_tts import ParlerTTSForConditionalGeneration, ParlerTTSConfig

path = r"S:\voice agent\Voice_Agent\Backend\.hf_cache\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca\model.safetensors"
model_id = "ai4bharat/indic-parler-tts"
cache_dir = "S:/voice agent/Voice_Agent/Backend/.hf_cache"

print("Loading config...")
config = ParlerTTSConfig.from_pretrained(model_id, cache_dir=cache_dir)
print("Config loaded!")

print("Initializing model...")
# Set default dtype to bfloat16 to save memory
torch.set_default_dtype(torch.bfloat16)
model = ParlerTTSForConditionalGeneration(config)
torch.set_default_dtype(torch.float32)
print("Model initialized!")

print("Loading state dict via NumPy...")
state_dict = {}
try:
    with safe_open(path, framework="numpy", device="cpu") as f:
        for i, key in enumerate(f.keys()):
            val_np = f.get_tensor(key)
            # Convert to torch tensor and cast to bfloat16
            val_torch = torch.from_numpy(val_np).to(torch.bfloat16)
            state_dict[key] = val_torch
            if i % 100 == 0:
                print(f"Loaded {i} tensors...")
    print("NumPy state dict loaded in memory!")

    print("Loading state dict into model...")
    model.load_state_dict(state_dict)
    print("SUCCESS: Model weights loaded successfully via custom NumPy loader!")
except Exception as e:
    import traceback
    traceback.print_exc()
