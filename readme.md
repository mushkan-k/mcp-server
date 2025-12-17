# MCP Ops Server (Python)


A unified MCP server exposing tools for Splunk, Kubernetes and Email.


## Endpoints
- `GET /health` health check
- `GET /list_tools` returns tools metadata
- `POST /invoke` invoke a tool `{ "tool": "<tool_name>", "params": {...} }`


## Run
1. Copy files into a project folder.
2. `cp .env.example .env` and fill credentials.
3. `python -m venv .venv && source .venv/bin/activate` (or use Windows equivalent)
4. `pip install -r requirements.txt`
5. `uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`


## Example invoke
```bash
curl -s -X POST http://localhost:8080/invoke -H 'Content-Type: application/json' -d '{"tool":"splunk.search","params":{"query":"search index=_internal | head 5"}}'