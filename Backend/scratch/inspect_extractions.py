import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

job_ids = ['581348a1-7491-4d37-a23c-2cf5142ff51d', '670f1e20-3beb-4a21-8036-63c50e4598e3']

for jid in job_ids:
    print(f"\n=================== JOB {jid} ===================")
    row = conn.execute("SELECT * FROM website_extractions WHERE job_id=? ORDER BY created_at DESC LIMIT 1", (jid,)).fetchone()
    if not row:
        print("No extraction found")
        continue
    
    ext_data = json.loads(row["extraction_json"])
    print("KEYS in extraction:", list(ext_data.keys()))
    print("company:", ext_data.get("company"))
    print("complete_knowledge_summary_markdown starts with:", str(ext_data.get("complete_knowledge_summary_markdown"))[:200])
    print("contact_info:", ext_data.get("contact_info"))

conn.close()
