from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, File, UploadFile, Query, Request

from app.core.config import settings
from app.core.errors import AppException, ErrorCodes
from app.core.trace import get_trace_id
from app.models.schemas import OcrResponse
from app.services.image_fetch import fetch_image_bytes

router = APIRouter(tags=["OCR"])


class OcrFromUrlRequest(BaseModel):
    image_url: str = Field(..., description="URL pública de la imagen")
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Headers opcionales (cookies, referer, auth). Útil para sitios que bloquean descargas.",
    )


@router.post("/v1/ocr", response_model=OcrResponse)
async def ocr_upload(
    request: Request,
    file: UploadFile = File(...),
    preprocess: bool = Query(True, description="Padding + resize inteligente"),
    blocks: bool = Query(True, description="Devuelve blocks con box/confidence"),
):
    if not file.filename:
        raise AppException(400, ErrorCodes.OCR_VALIDATION_400, "Validation failed", "Archivo sin nombre")

    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in settings.allowed_ext:
        raise AppException(
            415,
            ErrorCodes.OCR_UNSUPPORTED_415,
            "Unsupported media type",
            f"Formato no soportado: {ext}",
        )

    data = await file.read()
    if not data:
        raise AppException(400, ErrorCodes.OCR_VALIDATION_400, "Validation failed", "Archivo vacío")

    if len(data) > settings.max_bytes:
        raise AppException(
            413,
            ErrorCodes.OCR_TOO_LARGE_413,
            "Payload too large",
            f"El archivo excede {settings.max_file_mb}MB",
        )

    engine = request.app.state.ocr_engine
    out = engine.extract_from_bytes(data, preprocess=preprocess, return_blocks=blocks)

    return {"ok": True, "traceId": get_trace_id(), "data": out}


@router.post("/v1/ocr/from-url", response_model=OcrResponse)
async def ocr_from_url(
    request: Request,
    payload: OcrFromUrlRequest,
    preprocess: bool = Query(True, description="Padding + resize inteligente"),
    blocks: bool = Query(True, description="Devuelve blocks con box/confidence"),
):
    # 1) descargar imagen (con agente/headers + streaming + límite)
    img_bytes = await fetch_image_bytes(payload.image_url, extra_headers=payload.headers)

    # 2) OCR
    engine = request.app.state.ocr_engine
    out = engine.extract_from_bytes(img_bytes, preprocess=preprocess, return_blocks=blocks)

    return {"ok": True, "traceId": get_trace_id(), "data": out}