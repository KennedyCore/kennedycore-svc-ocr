from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, Request, Query

from app.services.ocr_engine import PaddleOcrEngine

router = APIRouter()

_engine: PaddleOcrEngine | None = None


def get_engine() -> PaddleOcrEngine:
    global _engine
    if _engine is None:
        _engine = PaddleOcrEngine(lang="es", drop_score=0.3)
    return _engine


ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
MAX_FILE_MB = 10


@router.post("/v1/ocr")
async def ocr_upload(
    request: Request,
    file: UploadFile = File(...),
    preprocess: bool = Query(True, description="Aplica padding + resize inteligente antes de OCR"),
    blocks: bool = Query(True, description="Devuelve bloques con box/confidence"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Formato no soportado: {ext}")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacío")

    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Archivo excede {MAX_FILE_MB}MB")

    trace_id = request.headers.get("X-Request-Id", "")

    try:
        engine = get_engine()
        out = engine.extract_from_bytes(data, preprocess=preprocess, return_blocks=blocks)

        return {
            "ok": True,
            "traceId": trace_id,
            "data": out,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))