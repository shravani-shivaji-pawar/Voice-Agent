import json
import os

if os.path.exists("db/agents.json"):
    try:
        with open("db/agents.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for agent in data:
            name = agent.get("name") or agent.get("agent_name", "")
            if "ira" in name.lower() or "ira" in str(agent.get("id", "")).lower():
                print("Found in agents.json:", agent)
    except Exception as e:
        print("Error parsing agents.json:", e)

# Also check individual json files
for f in os.listdir("db/agents"):
    if f.endswith(".json"):
        try:
            with open(os.path.join("db/agents", f), "r", encoding="utf-8") as file:
                data = json.load(file)
            name = data.get("agent_name", "")
            if "ira" in name.lower():
                print(f"Found in db/agents/{f}: Name={name}")
        except Exception:
            pass
