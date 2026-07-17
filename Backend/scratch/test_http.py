import httpx
import asyncio

async def main():
    url = "http://localhost:8000/api/intelligence/script-drafts/invalid-draft-id-for-testing"
    headers = {
        "X-Tenant-ID": "user-6e9697ec9f31",
        "X-User-Email": "shravani772004@gmail.com"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.delete(url, headers=headers)
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text}")
    except Exception as e:
        print(f"HTTP request failed: {e}")

asyncio.run(main())
