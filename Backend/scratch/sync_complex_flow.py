import json
import sqlite3
import os

db_path = "db/platform.db"
complex_flow_path = "db/agents/real_estate_sales.json"

with open(complex_flow_path, "r", encoding="utf-8") as f:
    complex_flow = json.load(f)

# The voice settings for Parler
parler_voice = {
    "voice_id": "parler-default",
    "tts_provider": "parler",
    "parler_description": "A young boy with a clear, calm, and moderate-paced voice speaking in Hindi."
}

# List of target agent IDs to copy the complex flow to
target_agent_ids = [
    "ea2e03c2-e6d0-4437-bebc-acd3eb2eb01a",
    "8e812315-ab39-4a87-8045-349ddf67dfd5",
    "tts-test-agent"
]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

for agent_id in target_agent_ids:
    # 1. Fetch current agent details from database if it exists
    row = conn.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not row:
        print(f"Agent {agent_id} not found in database, skipping database sync")
        continue
    agent_db = dict(row)
    
    # 2. Overwrite the JSON file
    json_file_path = f"db/agents/{agent_id}.json"
    agent_json = dict(complex_flow)
    agent_json["agent_id"] = agent_id
    agent_json["agent_name"] = agent_db.get("name") or agent_json.get("agent_name")
    agent_json["voice_id"] = parler_voice["voice_id"]
    agent_json["provider_config"] = {
        "stt_provider": agent_db.get("stt_provider") or "deepgram",
        "tts_provider": "parler",
        "voice_id": parler_voice["voice_id"],
        "parler_description": parler_voice["parler_description"]
    }
    
    with open(json_file_path, "w", encoding="utf-8") as out_f:
        json.dump(agent_json, out_f, indent=4, ensure_ascii=False)
    print(f"Overwrote JSON file for agent: {agent_id}")
    
    # 3. Update the database table
    conn.execute(
        """UPDATE agents 
           SET tts_provider = 'parler', 
               parler_description = ?, 
               script = ?, 
               language = 'Hindi + English' 
           WHERE id = ?""",
        (parler_voice["parler_description"], agent_json.get("global_prompt", ""), agent_id)
    )
    print(f"Updated database row for agent: {agent_id}")

conn.commit()
conn.close()
print("All agents successfully synchronized with the complex real estate sales flow!")
