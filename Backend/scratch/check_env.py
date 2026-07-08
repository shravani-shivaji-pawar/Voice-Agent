import urllib.request
import json
import os

print("--- ENV ---")
for k in ["TTS_PROVIDER", "STT_PROVIDER", "PORT", "BACKEND_API_URL"]:
    print(f"{k}: {os.getenv(k)}")

print("--- API FETCH ---")
try:
    port = os.getenv("PORT", "8000")
    url = f"http://127.0.0.1:{port}/api/agents/tts-test-agent"
    print(f"Querying: {url}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=2.0) as response:
        print("Status:", response.status)
        print("Response:", json.loads(response.read().decode()))
except Exception as e:
    print("Error querying API:", e)
