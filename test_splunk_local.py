# test_splunk_local.py
import asyncio
import os
from app.clients.splunk_mcp import SplunkMCP

async def main():
    base = os.getenv("SPLUNK_BASE_URL", "http://localhost:8089")
    token = os.getenv("SPLUNK_TOKEN", "")
    username = os.getenv("SPLUNK_USERNAME", "admin")
    password = os.getenv("SPLUNK_PASSWORD", "admin123")
    
    print("Using:", base)
    if token:
        print("Auth: Token")
        client = SplunkMCP(base, token=token, timeout=30)
    else:
        print("Auth: Basic Auth (username/password)")
        client = SplunkMCP(base, username=username, password=password, timeout=30)

    # Example queries - try simple first
    queries = [
        "search index=_internal | head 5",
        "search index=_internal error OR failure | head 5"
    ]

    for q in queries:
        print("\nRunning (raw output):", q)
        try:
            res = await client.search(q, timeout=30)
            print("-> Success. count:", res.get("count"))
            # print first raw event lines
            results = res.get("results", [])
            for i, r in enumerate(results[:5], 1):
                print(f"  raw {i}: {r[:200]}")
        except Exception as e:
            print("-> Exception from client:", e)

if __name__ == "__main__":
    asyncio.run(main())
