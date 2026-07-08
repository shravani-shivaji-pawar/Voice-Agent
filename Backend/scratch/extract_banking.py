import json
import os

os.makedirs("db/agents/banking", exist_ok=True)

with open("db/agents/finance.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

# Update metadata to reference banking/Arjun
schema["agent_name"] = "Arjun"
schema["conversation_flow_id"] = "flow_banking"

# 1. Build conversation.json
conversation = {
    "agent_name": schema.get("agent_name", "Arjun"),
    "voice_id": schema.get("voice_id", "11labs-06nek6zjTCD1vCbtc8bc"),
    "conversation_flow_id": schema.get("conversation_flow_id", "flow_banking"),
    "global_prompt": "You are Arjun from the Banking desk. Qualify customer credit interest, loan requirements, and callback preferences. Ask one question at a time.",
    "start_node_id": schema.get("conversationFlow", {}).get("start_node_id", "root_greeting"),
    "default_locale": schema.get("conversationFlow", {}).get("default_locale", "en"),
    "supported_locales": schema.get("conversationFlow", {}).get("supported_locales", ["en", "hi", "mr"])
}

# Include other root keys
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/banking/conversation.json", "w", encoding="utf-8") as f:
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

with open("db/agents/banking/nodes.json", "w", encoding="utf-8") as f:
    json.dump(nodes_out, f, indent=4, ensure_ascii=False)

with open("db/agents/banking/transitions.json", "w", encoding="utf-8") as f:
    json.dump(transitions_out, f, indent=4, ensure_ascii=False)

# 3. Build intents.json
intents = flow.get("intents", [
    {"id": "confirm", "examples": ["yes", "yeah", "yep", "sure", "correct", "haan", "han", "ho", "ji", "theek hai"]},
    {"id": "deny", "examples": ["no", "nope", "nah", "nahi", "nai", "nako"]},
    {"id": "provide_info", "examples": ["home loan", "50 lakh", "personal loan", "credit card"]}
])

with open("db/agents/banking/intents.json", "w", encoding="utf-8") as f:
    json.dump(intents, f, indent=4, ensure_ascii=False)

print("Banking agent split files extracted successfully.")
