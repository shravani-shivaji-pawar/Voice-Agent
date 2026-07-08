import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

job = conn.execute("SELECT * FROM website_scrape_jobs WHERE id='a9ede6a8-b3b7-4d5c-ab5a-6106ab3bb198'").fetchone()
if job:
    print(dict(job))
else:
    print("Job not found")

conn.close()
