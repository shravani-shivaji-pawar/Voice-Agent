from safetensors import safe_open

path = r"S:\voice agent\Voice_Agent\Backend\.hf_cache\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca\model.safetensors"
with safe_open(path, framework="numpy", device="cpu") as f:
    dtypes = {}
    for key in f.keys():
        tensor = f.get_tensor(key)
        dtypes[str(tensor.dtype)] = dtypes.get(str(tensor.dtype), 0) + 1

print("Tensor counts by NumPy data type:", dtypes)
