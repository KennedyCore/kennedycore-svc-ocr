from __future__ import annotations

from pathlib import Path
from typing import Tuple
from uuid import uuid4

from fastapi import UploadFile

from app.core.errors import AppError, ErrorCodes

CHUNK_SIZE = 1024 * 1024  # 1MB

def _ext(filename: str) -> str:
    return Path(filename).suffix.lower()

async def save_upload_file(
    upload: UploadFile,
    dst_dir: Path,
    max_bytes: int,
    allowed_ext: set[str],
) -> Tuple[Path, str]:
    if not upload.filename:
        raise AppError(400, ErrorCodes.VALIDATION_400, "Invalid request", "File has no name")

    ext = _ext(upload.filename)
    if ext not in allowed_ext:
        raise AppError(415, ErrorCodes.UNSUPPORTED_415, "Unsupported media type", f"Unsupported file extension: {ext}")

    dst_name = f"{uuid4().hex}{ext}"
    dst_path = dst_dir / dst_name

    size = 0
    with dst_path.open("wb") as f:
        while True:
            chunk = await upload.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                try:
                    dst_path.unlink(missing_ok=True)
                finally:
                    raise AppError(413, ErrorCodes.TOO_LARGE_413, "Payload too large", f"Max file size is {max_bytes} bytes")
            f.write(chunk)

    await upload.close()
    return dst_path, dst_name
