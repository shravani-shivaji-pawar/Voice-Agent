import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

agent = conn.execute("SELECT * FROM agents WHERE id='b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc'").fetchone()
if agent:
    print(dict(agent))
else:
    print("Agent not found")

conn.close()
