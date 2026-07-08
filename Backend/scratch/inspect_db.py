import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
print(f"Connecting to database at {db_path} (exists: {db_path.exists()})")

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

print("\n--- WEBSITE SCRAPE JOBS ---")
jobs = conn.execute("SELECT id, url, status, error, progress, created_at FROM website_scrape_jobs ORDER BY created_at DESC LIMIT 5").fetchall()
for job in jobs:
    print(dict(job))

print("\n--- GENERATED SCRIPT DRAFTS ---")
drafts = conn.execute("SELECT id, job_id, status, created_at, knowledge_json FROM generated_script_drafts ORDER BY created_at DESC LIMIT 5").fetchall()
for draft in drafts:
    d = dict(draft)
    k_json = d.pop("knowledge_json")
    try:
        k = json.loads(k_json)
        d["has_summary"] = bool(k.get("complete_knowledge_summary_markdown"))
        d["company_name"] = k.get("company", {}).get("name")
        d["num_products"] = len(k.get("products_or_services") or [])
    except Exception as e:
        d["has_summary"] = f"Error: {e}"
    print(d)

conn.close()
