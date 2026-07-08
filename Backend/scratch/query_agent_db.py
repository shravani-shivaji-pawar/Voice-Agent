import sqlite3
from pathlib import Path
import json

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

row = conn.execute("SELECT * FROM agents WHERE id=?", ("tts-test-agent",)).fetchone()
if row:
    print(dict(row))
else:
    print("Agent 'tts-test-agent' not found in database.")
conn.close()
