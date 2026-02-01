from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class OcrBlock(BaseModel):
    text: str
    confidence: float
    box: List[List[int]]


class OcrData(BaseModel):
    text: str
    blocks: List[OcrBlock]
    preprocess: Optional[Dict[str, Any]] = None


class OcrResponse(BaseModel):
    ok: bool
    traceId: str
    data: OcrData