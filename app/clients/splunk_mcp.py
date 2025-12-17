import time
import httpx
import asyncio
from typing import Any, Dict, List, Optional
from httpx import BasicAuth


class SplunkMCP:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.auth = BasicAuth(username, password) if username and password else None
        self.timeout = timeout

    def _headers(self, content_type="application/x-www-form-urlencoded") -> Dict[str, str]:
        headers = {"Content-Type": content_type}
        if self.token:
            headers["Authorization"] = f"Splunk {self.token}"
        return headers

    async def create_search_job(
        self, search: str, earliest_time: Optional[str], latest_time: Optional[str]
    ) -> str:
        body = {
            "search": search,
            "output_mode": "json",
            "earliest_time": earliest_time,
            "latest_time": latest_time,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/services/search/jobs",
                data=body,
                headers=self._headers(),
                auth=self.auth,
            )
            r.raise_for_status()
            sid = r.json().get("sid")
            if not sid:
                raise RuntimeError(f"Failed to create search job: {r.text}")
            return sid

    async def is_job_done(self, sid: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base_url}/services/search/jobs/{sid}",
                headers=self._headers(),
                auth=self.auth,
                params={"output_mode": "json"},
            )
            r.raise_for_status()
            entry = r.json().get("entry", [{}])
            return entry[0].get("content", {}).get("isDone", False)

    async def get_results(self, sid: str, endpoint: str = "results", count: int = 50) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base_url}/services/search/jobs/{sid}/{endpoint}",
                headers=self._headers(),
                auth=self.auth,
                params={"output_mode": "json", "count": count},
            )
            r.raise_for_status()
            return r.json().get("results", [])

    async def search(
        self, query: str, earliest_time: Optional[str] = "-1h", latest_time: Optional[str] = "now", timeout: int = 30
    ) -> Dict[str, Any]:
        sid = await self.create_search_job(query, earliest_time, latest_time)
        deadline = time.time() + timeout

        while time.time() < deadline:
            if await self.is_job_done(sid):
                await asyncio.sleep(2.0)
                results = await self.get_results(sid)
                return {"items": results, "count": len(results)}
            await asyncio.sleep(1.0)

        return {"items": [], "count": 0, "message": "Search job timed out"}

    async def ingest_event(self, event: Dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(
                f"{self.base_url}/services/collector/event",
                json=event,
                headers=self._headers(content_type="application/json"),
            )
            r.raise_for_status()
            return r.text