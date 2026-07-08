import json
import os

agents_dir = "db/agents"
for f in os.listdir(agents_dir):
    if f.endswith(".json") and not f.endswith(".flow.v2.json"):
        path = os.path.join(agents_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            print(f"File: {f} -> Name: {data.get('agent_name')} | ID/Flow ID: {data.get('conversation_flow_id')} | Type: {data.get('agent_metadata', {}).get('agent_type') or data.get('agent_type')}")
        except Exception as e:
            print(f"Error reading {f}: {e}")
