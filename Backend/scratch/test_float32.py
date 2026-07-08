import time
import os
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
from dotenv import load_dotenv

# Load env variables including HF token
load_dotenv()

os.environ["ONEDNN_MAX_CPU_ISA"] = "AVX2"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

model_id = "ai4bharat/indic-parler-tts"

print("Loading model in float32...")
t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = ParlerTTSForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True
).to("cpu")
print(f"Loaded in {time.time() - t0:.2f} seconds.")

description = "A young boy with a clear, calm, and moderate-paced voice speaking in Hindi."
text = "नमस्ते, मैं नेहा हूँ। आप कैसे हैं?"

print("Generating speech...")
t1 = time.time()
description_ids = tokenizer(description, return_tensors="pt").input_ids
prompt_ids = tokenizer(text, return_tensors="pt").input_ids

with torch.no_grad():
    generation = model.generate(
        input_ids=description_ids,
        prompt_input_ids=prompt_ids
    )

duration = time.time() - t1
audio_len = generation.shape[-1] / model.config.sampling_rate
print(f"Generated {audio_len:.2f} seconds of audio in {duration:.2f} seconds. Speed factor: {audio_len / duration:.2f}x")
