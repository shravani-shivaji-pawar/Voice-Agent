import httpx
import asyncio
import sys

async def main():
    base_url = "http://localhost:8000"
    headers = {
        "X-Tenant-ID": "user-6e9697ec9f31",
        "X-User-Email": "shravani772004@gmail.com",
        "Content-Type": "application/json"
    }
    
    agent_id = "b848f004-1cc1-4c7e-9dd4-749ecfd9c4fc"
    
    print("\n1. Creating scrape job...")
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            f"{base_url}/api/intelligence/scrape-jobs",
            headers=headers,
            json={
                "url": "https://google.com",
                "agentId": agent_id,
                "clientId": "user-6e9697ec9f31",
                "requestedBy": "shravani772004@gmail.com",
                "reuseExisting": False
            }
        )
        print("Create response:", res.status_code, res.text)
        job = res.json()
        job_id = job["id"]
        
        print("\n2. Dispatching scrape job...")
        res = await client.post(
            f"{base_url}/api/intelligence/scrape-jobs/{job_id}/dispatch",
            headers=headers,
            json={
                "industryHint": "education",
                "requestedBy": "shravani772004@gmail.com"
            }
        )
        print("Dispatch response:", res.status_code, res.text)
        
        print("\n3. Polling scrape job status...")
        for attempt in range(60):
            await asyncio.sleep(1.5)
            res = await client.get(f"{base_url}/api/intelligence/scrape-jobs/{job_id}", headers=headers)
            job_status = res.json()
            print(f"Attempt {attempt+1}: status={job_status.get('status')} progress={job_status.get('progress')}")
            if job_status.get("status") in ["completed", "failed", "cancelled"]:
                break
        
        if job_status.get("status") != "completed":
            print("Crawl did not complete successfully.")
            return
            
        print("\n4. Creating script draft...")
        res = await client.post(
            f"{base_url}/api/intelligence/script-drafts",
            headers=headers,
            json={
                "jobId": job_id,
                "agentId": agent_id,
                "industryHint": "education"
            }
        )
        print("Create draft response code:", res.status_code)
        draft = res.json()
        knowledge = draft.get("knowledge", {})
        summary = knowledge.get("complete_knowledge_summary_markdown")
        print("\nSUMMARY GENERATED:")
        print(summary)
        print("\nKEYS in knowledge:", list(knowledge.keys()))
        print("has_summary:", bool(summary))

asyncio.run(main())
