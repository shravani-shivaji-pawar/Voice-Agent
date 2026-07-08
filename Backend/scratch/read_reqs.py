with open("requirements.txt", "r", encoding="utf-16") as f:
    content = f.read()

for line in content.splitlines():
    if "json" in line or "schema" in line:
        print(line)
