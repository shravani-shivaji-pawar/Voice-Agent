import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

job_ids = ['30801c46-085b-4d94-93c6-ca32712dacab', '69872768-333a-4af8-9ff3-c8dac52969ed']

for jid in job_ids:
    print(f"\n=================== JOB {jid} ===================")
    job = conn.execute("SELECT * FROM website_scrape_jobs WHERE id=?", (jid,)).fetchone()
    print("JOB:", dict(job) if job else "Not found")
    
    print("\nEVENTS:")
    events = conn.execute("SELECT event_type, status, metadata_json, created_at FROM website_scrape_job_events WHERE job_id=? ORDER BY created_at ASC", (jid,)).fetchall()
    for e in events:
        d = dict(e)
        d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
        print(d)

conn.close()
