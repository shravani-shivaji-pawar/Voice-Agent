import shutil
import os

src_dir = "db/agents/ira"
dest_dir = "db/agents/b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc"

os.makedirs(dest_dir, exist_ok=True)
for item in os.listdir(src_dir):
    s = os.path.join(src_dir, item)
    d = os.path.join(dest_dir, item)
    shutil.copy2(s, d)

print("Split files copied successfully to UUID directory.")
