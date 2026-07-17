import json
import os

os.makedirs("db/agents/ira", exist_ok=True)

with open("db/agents/b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# 1. Build conversation.json
flow = schema.get("conversationFlow", {})
conversation = {
    "agent_name": schema.get("agent_name", "ira"),
    "voice_id": schema.get("voice_id", "11labs-06nek6zjTCD1vCbtc8bc"),
    "conversation_flow_id": flow.get("conversation_flow_id", "flow_ira"),
    "global_prompt": flow.get("global_prompt", "You are an education counselling voice agent. Understand course interest and connect them with counsellor."),
    "start_node_id": flow.get("start_node_id", "root_greeting"),
    "default_locale": flow.get("default_locale", "en"),
    "supported_locales": flow.get("supported_locales", ["en", "hi", "mr"])
}

# Include other root keys
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/ira/conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=4, ensure_ascii=False)

# 2. Build nodes.json and transitions.json
nodes = flow.get("nodes", [])

nodes_out = []
transitions_out = []

for node in nodes:
    node_id = node["id"]
    compiled_node = dict(node)
    
    # Extract edges to transitions.json
    edges = compiled_node.pop("edges", [])
    if edges:
        node_transitions = []
        for edge in edges:
            transition = {
                "id": edge.get("id"),
                "intent": edge.get("condition"),
                "target": edge.get("destination_node_id"),
                "condition": edge.get("condition")
            }
            node_transitions.append(transition)
        
        transitions_out.append({
            "from_node_id": node_id,
            "transitions": node_transitions
        })
        
    nodes_out.append(compiled_node)

with open("db/agents/ira/nodes.json", "w", encoding="utf-8") as f:
    json.dump(nodes_out, f, indent=4, ensure_ascii=False)

with open("db/agents/ira/transitions.json", "w", encoding="utf-8") as f:
    json.dump(transitions_out, f, indent=4, ensure_ascii=False)

# 3. Build intents.json
intents = flow.get("intents", [
    {"id": "confirm", "examples": ["yes", "yeah", "yep", "sure", "correct", "haan", "han", "ho", "ji", "theek hai"]},
    {"id": "deny", "examples": ["no", "nope", "nah", "nahi", "nai", "nako"]},
    {"id": "provide_info", "examples": ["computer science", "MBA", "next month", "online classes"]}
])

with open("db/agents/ira/intents.json", "w", encoding="utf-8") as f:
    json.dump(intents, f, indent=4, ensure_ascii=False)

print("Ira agent split files extracted successfully.")
