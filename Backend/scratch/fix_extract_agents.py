import json
import os

# 1. Real Estate
with open("Updated_Real_Estate_Agent.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

flow = schema.get("conversationFlow", {})
conversation = {
    "agent_name": schema.get("agent_name", "Neha"),
    "voice_id": schema.get("voice_id", "en-IN-NeerjaNeural"),
    "conversation_flow_id": flow.get("conversation_flow_id", "flow_real_estate"),
    "global_prompt": flow.get("global_prompt", "You are Neha, a real estate agent. Help the user qualify their interest, budget, location, and preferred visit time."),
    "start_node_id": flow.get("start_node_id", "node-1767592854176"),
    "default_locale": flow.get("default_locale", "en"),
    "supported_locales": flow.get("supported_locales", ["en", "hi", "mr"])
}
# Add other keys
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/real_estate/conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=4, ensure_ascii=False)

# 2. Healthcare
with open("db/agents/healthcare.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

flow = schema.get("conversationFlow", {})
conversation = {
    "agent_name": schema.get("agent_name", "Maya"),
    "voice_id": schema.get("voice_id", "en-IN-NeerjaNeural"),
    "conversation_flow_id": flow.get("conversation_flow_id", "flow_healthcare"),
    "global_prompt": flow.get("global_prompt", "You are Maya from Cosmic Clinic. Qualify appointments, symptoms, and times."),
    "start_node_id": flow.get("start_node_id", "root_greeting"),
    "default_locale": flow.get("default_locale", "en"),
    "supported_locales": flow.get("supported_locales", ["en", "hi", "mr"])
}
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/healthcare/conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=4, ensure_ascii=False)

# 3. Banking
with open("db/agents/finance.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

flow = schema.get("conversationFlow", {})
conversation = {
    "agent_name": "Arjun",
    "voice_id": schema.get("voice_id", "11labs-06nek6zjTCD1vCbtc8bc"),
    "conversation_flow_id": "flow_banking",
    "global_prompt": "You are Arjun from the Banking desk. Qualify customer credit interest, loan requirements, and callback preferences. Ask one question at a time.",
    "start_node_id": flow.get("start_node_id", "root_greeting"),
    "default_locale": flow.get("default_locale", "en"),
    "supported_locales": flow.get("supported_locales", ["en", "hi", "mr"])
}
for key, val in schema.items():
    if key not in ["conversationFlow", "agent_name", "voice_id", "global_prompt"]:
        conversation[key] = val

with open("db/agents/banking/conversation.json", "w", encoding="utf-8") as f:
    json.dump(conversation, f, indent=4, ensure_ascii=False)

print("Agent configurations regenerated successfully.")
