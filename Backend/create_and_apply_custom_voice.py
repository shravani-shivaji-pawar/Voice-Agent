import os
import sqlite3
import json
import httpx
from dotenv import load_dotenv

def main():
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY not found in .env file.")
        return

    print("Step 1: Requesting Voice Design from ElevenLabs...")
    headers = {"xi-api-key": api_key}
    
    design_payload = {
        "voice_description": "A warm, friendly, clear female voice speaking with a natural Indian accent.",
        "text": "Hello! This is a test of your custom Indian AI voice. This voice has been generated via the ElevenLabs Voice Design API. It will be used for testing and validating the real estate voice calling agent pipeline. Thank you!"
    }
    
    try:
        r = httpx.post(
            "https://api.elevenlabs.io/v1/text-to-voice/design",
            headers=headers,
            json=design_payload,
            timeout=15.0
        )
        if r.status_code != 200:
            print(f"[ERROR] Voice design API returned status {r.status_code}")
            print(r.text)
            return
            
        data = r.json()
        previews = data.get("previews") or []
        if not previews:
            print("[ERROR] No voice previews returned from the ElevenLabs Voice Design API.")
            return
            
        generated_voice_id = previews[0]["generated_voice_id"]
        print(f"[OK] Preview generated successfully! Voice design preview ID: {generated_voice_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to request voice design: {e}")
        return

    print("\nStep 2: Saving custom designed voice to your Voice Lab...")
    save_payload = {
        "voice_name": "Neha Custom Indian Female",
        "voice_description": "Custom Indian voice designed via API",
        "generated_voice_id": generated_voice_id
    }
    
    try:
        r = httpx.post(
            "https://api.elevenlabs.io/v1/text-to-voice",
            headers=headers,
            json=save_payload,
            timeout=15.0
        )
        if r.status_code != 200:
            print(f"[ERROR] Saving voice API returned status {r.status_code}")
            print(r.text)
            return
            
        res_data = r.json()
        new_voice_id = res_data.get("voice_id")
        if not new_voice_id:
            print("[ERROR] ElevenLabs did not return a voice_id for the saved voice.")
            return
            
        print(f"[SUCCESS] Voice saved to your Voice Lab. Voice ID: {new_voice_id}")
        
    except Exception as e:
        print(f"[ERROR] Failed to save voice to Voice Lab: {e}")
        return

    print("\nStep 3: Updating local SQLite database and agent configuration files...")
    
    # 1. Update database
    try:
        db_path = "db/platform.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE agents SET elevenlabs_voice_id = ? WHERE id IN ('tts-test-agent', 'test-agent')",
                (new_voice_id,)
            )
            conn.commit()
            print(f"[OK] Database updated for agents 'tts-test-agent' and 'test-agent' in {db_path} ({cursor.rowcount} rows affected).")
            conn.close()
        else:
            print(f"[WARNING] Database file not found at {db_path}.")
    except Exception as e:
        print(f"[ERROR] Database update failed: {e}")

    # 2. Update JSON files
    json_files = ["db/agents/tts-test-agent.json", "db/agents/test-agent.json"]
    for file_path in json_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                if "provider_config" in config:
                    config["provider_config"]["elevenlabs_voice_id"] = new_voice_id
                    
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                    
                print(f"[OK] Updated Voice ID in configuration file: {file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to update file {file_path}: {e}")

    print("\n[SUCCESS] All done! Please refresh the agent page in the browser and start a new talk-live session. Your custom Indian voice will speak instantly!")

if __name__ == "__main__":
    main()
