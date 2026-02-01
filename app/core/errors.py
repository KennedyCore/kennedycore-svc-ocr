from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppException(Exception):
    status: int
    code: str
    title: str
    detail: str


class ErrorCodes:
    OCR_VALIDATION_400 = "OCR-VALIDATION-400"
    OCR_UNSUPPORTED_415 = "OCR-UNSUPPORTED-415"
    OCR_TOO_LARGE_413 = "OCR-TOO-LARGE-413"
    OCR_FETCH_400 = "OCR-FETCH-400"
    OCR_FETCH_502 = "OCR-FETCH-502"
    OCR_INTERNAL_500 = "OCR-ERR-500"