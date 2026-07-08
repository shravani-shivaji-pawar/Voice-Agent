import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "db" / "platform.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

domains = ['google.com', 'stripe.com']
for domain in domains:
    print(f"Clearing cache for {domain}...")
    # Find jobs
    jobs = cursor.execute("SELECT id FROM website_scrape_jobs WHERE domain=?", (domain,)).fetchall()
    job_ids = [j[0] for j in jobs]
    
    if job_ids:
        # Delete drafts
        cursor.execute(f"DELETE FROM generated_script_drafts WHERE job_id IN ({','.join(['?']*len(job_ids))})", job_ids)
        # Delete extractions
        cursor.execute(f"DELETE FROM website_extractions WHERE job_id IN ({','.join(['?']*len(job_ids))})", job_ids)
        # Delete jobs
        cursor.execute(f"DELETE FROM website_scrape_jobs WHERE id IN ({','.join(['?']*len(job_ids))})", job_ids)
        print(f"Deleted {len(job_ids)} jobs and related entries.")
    else:
        print("No cached jobs found.")

conn.commit()
conn.close()
print("Cache cleared successfully.")
