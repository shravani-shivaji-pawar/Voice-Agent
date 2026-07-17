with open("llm/state_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "json_path" in line:
        print(f"{i+1}: {line.strip()}")
