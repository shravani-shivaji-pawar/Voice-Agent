import urllib.request
import ssl

url = "https://www.cisco.com"
headers = {
    "User-Agent": "VoiceAgentWebsiteIntelligence/1.0",
    "Accept": "text/html,text/plain,application/xhtml+xml;q=0.9,*/*;q=0.5",
}

print("Trying with standard ssl context...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Success! Status:", response.status)
except Exception as e:
    print("Failed standard with:", type(e), str(e))
    print("\nRetrying with unverified context...")
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            print("Success with unverified context! Status:", response.status)
            print("Content Type:", response.headers.get("content-type"))
    except Exception as e2:
        print("Failed unverified with:", type(e2), str(e2))
