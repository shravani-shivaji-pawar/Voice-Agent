import os
from safetensors import safe_open
import torch

path = r"S:\voice agent\Voice_Agent\Backend\.hf_cache\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca\model.safetensors"
print("Checking file path exists:", os.path.exists(path))
print("Opening with safe_open...")
with safe_open(path, framework="numpy", device="cpu") as f:
    keys = list(f.keys())
    print("Found keys:", len(keys))
    tensor_name = keys[0]
    tensor_np = f.get_tensor(tensor_name)
    print(f"Loaded tensor {tensor_name}: shape={tensor_np.shape}, dtype={tensor_np.dtype}")
    # Convert to torch tensor
    tensor_torch = torch.from_numpy(tensor_np)
    print("Converted to torch! shape =", tensor_torch.shape)
