import json

with open("Updated_Real_Estate_Agent.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Agent Keys:", list(data.keys()))
if "conversationFlow" in data:
    flow = data["conversationFlow"]
    print("ConversationFlow Keys:", list(flow.keys()))
    print("First Node:", json.dumps(flow["nodes"][0], indent=2))
