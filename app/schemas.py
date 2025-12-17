from pydantic import BaseModel
from typing import Any, Dict, Optional


class InvokeRequest(BaseModel):
    tool: str
params: Optional[Dict[str, Any]] = {}


class InvokeResponse(BaseModel):
    status: str
result: Optional[Any] = None
error: Optional[str] = None