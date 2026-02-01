from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.trace import get_trace_id, new_trace_id, set_trace_id
from app.core.errors import AppException, ErrorCodes
from app.api.v1.router import router as v1_router
from app.services.ocr_engine import PaddleOcrEngine


PROBLEM_JSON = "application/problem+json"


def problem_response(request: Request, status: int, code: str, title: str, detail: str, errors=None):
    trace_id = get_trace_id()
    body = {
        "type": f"{settings.problem_base_url}/{code.lower()}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "traceId": trace_id,
        "code": code,
        "errors": errors or [],
    }
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("X-Request-Id", "").strip()
        tid = incoming if incoming else new_trace_id()
        set_trace_id(tid)

        response = await call_next(request)
        response.headers["X-Request-Id"] = tid
        return response


app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(TraceIdMiddleware)
app.include_router(v1_router)


@app.on_event("startup")
def startup():
    app.state.ocr_engine = PaddleOcrEngine()
    app.state.ready = True

@app.get("/ping")
def ping():
    return {"ok": True, "service": settings.app_name, "traceId": get_trace_id()}


@app.get("/info")
def info():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/health")
def health():
    return {"ok": True, "ready": bool(getattr(app.state, "ready", False)), "traceId": get_trace_id()}


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return problem_response(request, exc.status, exc.code, exc.title, exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        loc = ".".join([str(x) for x in e.get("loc", [])])
        errors.append({"field": loc, "message": e.get("msg", "Invalid value")})

    return problem_response(
        request,
        400,
        ErrorCodes.OCR_VALIDATION_400,
        "Validation failed",
        "One or more fields are invalid.",
        errors=errors,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return problem_response(
        request,
        500,
        ErrorCodes.OCR_INTERNAL_500,
        "Internal error",
        "An unexpected error occurred.",
    )