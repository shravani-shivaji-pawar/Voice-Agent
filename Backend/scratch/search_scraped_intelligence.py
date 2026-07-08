import os

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") and not "venv" in root:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "intelligence" in content or "summary" in content or "crawled" in content:
                    print(f"File: {path}")
                    # print lines containing these words
                    lines = content.splitlines()
                    for idx, line in enumerate(lines):
                        if any(w in line for w in ["intelligence", "summary", "crawled"]):
                            print(f"  Line {idx+1}: {line.strip()}")
            except Exception:
                pass
