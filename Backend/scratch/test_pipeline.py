import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from db.db_manager import DatabaseManager
from intelligence.pipeline import WebsiteIntelligencePipeline

logging.basicConfig(level=logging.INFO)

async def main():
    db = DatabaseManager()
    pipeline = WebsiteIntelligencePipeline(db)
    
    # Create a test client and agent if they don't exist
    await db.create_client("test-client", {"name": "Test Client", "email": "test@example.com"})
    await db.create_agent("test-agent", {
        "name": "Test Agent", "voice": "voice", "language": "English",
        "client_id": "test-client", "agent_type": "real_estate_sales"
    })
    
    # Create scrape job
    job = await pipeline.create_job(
        client_id="test-client",
        agent_id="test-agent",
        url="http://example.com",
        reuse_existing=False
    )
    print(f"Created job: {job['id']}")
    
    # Run job
    print("Running job...")
    res = await pipeline.run_job(job_id=job["id"], industry_hint="real_estate_sales")
    print("Run job result keys:", res.keys())
    
    # Get extraction
    latest = await db.get_latest_scrape_extraction(job["id"])
    if latest:
        ext = latest["extraction"]
        print("has_summary:", bool(ext.get("complete_knowledge_summary_markdown")))
        print("company_name:", ext.get("company", {}).get("name"))
        print("summary:", str(ext.get("complete_knowledge_summary_markdown"))[:300])
    else:
        print("No extraction found in DB")

asyncio.run(main())
