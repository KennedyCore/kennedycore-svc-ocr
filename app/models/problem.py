from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    timestamp: str
    traceId: str
    code: str
    errors: List[Dict[str, Any]] = []