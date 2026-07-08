with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
for i, line in enumerate(lines):
    if '@app.post("/api/agents"' in line or '@app.post("/api/agents)' in line or 'async def create_agent' in line:
        print(f"Line {i+1}: {line}")
        # print subsequent 30 lines
        for j in range(i, min(i+40, len(lines))):
            print(f"  {j+1}: {lines[j]}")
