import os
from safetensors import safe_open
import torch

snapshot_dir = r"S:\voice agent\Voice_Agent\Backend\.hf_cache\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca"
safetensors_path = os.path.join(snapshot_dir, "model.safetensors")
pytorch_bin_path = os.path.join(snapshot_dir, "pytorch_model.bin")

print("Checking files...")
print("Safetensors path:", safetensors_path)
print("Safetensors exists:", os.path.exists(safetensors_path))

print("Loading safetensors via NumPy...")
state_dict = {}
with safe_open(safetensors_path, framework="numpy", device="cpu") as f:
    for i, key in enumerate(f.keys()):
        val_np = f.get_tensor(key)
        # Convert to torch tensor in bfloat16 to save memory
        val_torch = torch.from_numpy(val_np).to(torch.bfloat16)
        state_dict[key] = val_torch
        if i % 100 == 0:
            print(f"Loaded {i} tensors...")

print("Successfully loaded all tensors in memory!")
print("Saving weights as pytorch_model.bin...")
torch.save(state_dict, pytorch_bin_path)
print("Saved pytorch_model.bin successfully!")
