from __future__ import annotations

from pydantic import BaseModel, Field

class OcrBlock(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: list[list[float]]

class OcrData(BaseModel):
    text: str
    blocks: list[OcrBlock]

class SuccessResponse(BaseModel):
    ok: bool = True
    traceId: str
    data: OcrData
