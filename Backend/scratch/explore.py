import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find lines matching _resolve_schema
lines = content.splitlines()
for i, line in enumerate(lines):
    if "_resolve_schema" in line:
        print(f"{i+1}: {line}")
