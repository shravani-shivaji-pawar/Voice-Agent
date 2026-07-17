import sqlite3
import json
import os
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))

# Run ALTER TABLE just to make sure parler_description column exists
try:
    conn.execute("ALTER TABLE agents ADD COLUMN parler_description TEXT")
    print("Added parler_description column.")
except sqlite3.OperationalError:
    print("parler_description column already exists.")

# Insert or Replace agent
agent_data = {
    "id": "tts-test-agent",
    "name": "Neha — Real Estate Specialist (Parler TTS)",
    "voice": "parler-default",
    "language": "Hindi + English",
    "max_duration": 120,
    "provider": "Pipecat-AI Execution",
    "stt_provider": "deepgram",
    "tts_provider": "parler",
    "parler_description": "A young boy with a clear, calm, and moderate-paced voice speaking in Hindi.",
    "script": "You are Neha from the Real Estate AI team. Qualify property leads with a warm, charismatic tone. Detect language naturally (English, Hinglish, Marathi).",
    "data_fields": json.dumps(["Name", "Location", "Budget", "Property Type", "Interested"]),
    "schema_path": "db\\agents\\tts-test-agent.json",
    "certification_status": "Testing"
}

try:
    conn.execute("""
        INSERT OR REPLACE INTO agents (
            id, name, voice, language, max_duration, provider, stt_provider, 
            tts_provider, parler_description, script, data_fields, schema_path, 
            certification_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_data["id"], agent_data["name"], agent_data["voice"], agent_data["language"],
        agent_data["max_duration"], agent_data["provider"], agent_data["stt_provider"],
        agent_data["tts_provider"], agent_data["parler_description"], agent_data["script"],
        agent_data["data_fields"], agent_data["schema_path"], agent_data["certification_status"]
    ))
    conn.commit()
    print("Test agent inserted/updated successfully in platform.db.")
except Exception as e:
    print(f"Error inserting test agent: {e}")
finally:
    conn.close()
