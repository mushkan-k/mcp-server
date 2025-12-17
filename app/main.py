from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from .schemas import InvokeRequest, InvokeResponse
from . import tools
import uvicorn


app = FastAPI(title='MCP Ops Server')


@app.get('/health')
async def health():
    return { 'status': 'ok' }


@app.get('/list_tools')
async def list_tools():
    resp = {}
    for name, meta in tools.TOOLS.items():
        resp[name] = { 'description': meta.get('description'), 'params': meta.get('params') }
    return resp


class InvokeBody(BaseModel):
    tool: str
    params: Dict[str, Any] 


@app.post('/invoke')
async def invoke(body: InvokeBody):
    tool_name = body.tool
    params = body.params or {}
    meta = tools.TOOLS.get(tool_name)
    if not meta:
        raise HTTPException(status_code=400, detail=f'Tool {tool_name} not found')
    handler = meta['handler']
    try:
        result = await handler(params)

        # If tool returns an error
        if isinstance(result, dict) and result.get("status") == "error":
            return InvokeResponse(status="error", error=result.get("message", "Unknown error")).dict()

        # Normalize result
        if isinstance(result, dict):
            # If it's already in Splunk format
            if "sid" in result and "results" in result:
                return {
                    "status": "success",
                    "sid": result["sid"],
                    "results": result["results"]
                }
            # Otherwise, treat it as a generic result
            return {
                "status": "success",
                "result": result
            }

        # Fallback
        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        return InvokeResponse(status="error", error=str(e)).dict()


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8081'))
    uvicorn.run('app.main:app', host=host, port=port, reload=True)