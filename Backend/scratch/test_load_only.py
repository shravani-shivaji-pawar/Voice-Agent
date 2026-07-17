import os
from safetensors.torch import load_file

path = r"S:\voice agent\Voice_Agent\Backend\.hf_cache\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca\model.safetensors"
print("Checking file path exists:", os.path.exists(path))
print("Loading safetensors file...")
weights = load_file(path)
print("Loaded! Number of tensors:", len(weights))
