import json
import os

os.makedirs("db/agents/real_estate", exist_ok=True)

with open("Updated_Real_Estate_Agent.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# 1. Build conversation.json
conversation = {
    "agent_name": schema.get("agent_name", "Neha"),
    "voice_id": schema.get("voice_id", "en-IN-NeerjaNeural"),
    "conversation_flow_id": schema.get("conversation_flow_id", "flow_real_estate"),
    "global_prompt": schema.get("global_prompt", ""),
    "start_node_id": schema.get("conversationFlow", {}).get("start_node_id", "node-1767592854176"),
    "default_locale": schema.get("conversationFlow", {}).get("default_locale", "en"),
    "supported_locales": schema.get("conversationFlow", {}).get("supported_locales", ["en", "hi", "mr"])
}
# Include other root keys
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/real_estate/conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=4, ensure_ascii=False)

# 2. Build nodes.json and transitions.json
flow = schema.get("conversationFlow", {})
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

with open("db/agents/real_estate/nodes.json", "w", encoding="utf-8") as f:
    json.dump(nodes_out, f, indent=4, ensure_ascii=False)

with open("db/agents/real_estate/transitions.json", "w", encoding="utf-8") as f:
    json.dump(transitions_out, f, indent=4, ensure_ascii=False)

# 3. Build intents.json
intents = flow.get("intents", [
    {"id": "confirm", "examples": ["yes", "yeah", "yep", "sure", "correct", "haan", "han", "ho", "ji", "theek hai"]},
    {"id": "deny", "examples": ["no", "nope", "nah", "nahi", "nai", "nako"]},
    {"id": "deny_identity", "examples": ["wrong number", "wrong person", "not Prashant", "this is not him"]},
    {"id": "deny_interest", "examples": ["not interested", "not looking", "no requirement", "dont need"]},
    {"id": "deny_time", "examples": ["busy", "call later", "not now", "in a meeting", "driving"]},
    {"id": "provide_info", "examples": ["my budget is 50 lakh", "looking in Wakad", "want to buy a 2 BHK"]}
])

with open("db/agents/real_estate/intents.json", "w", encoding="utf-8") as f:
    json.dump(intents, f, indent=4, ensure_ascii=False)

print("Real Estate agent split files extracted successfully.")
