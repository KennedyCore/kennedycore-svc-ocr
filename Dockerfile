# syntax=docker/dockerfile:1.7
#
# KennedyCore OCR Service - Dockerfile (prod-ready)
# - Multi-stage build
# - Non-root user
# - CI-enforced deploy (tests must pass)
#

# --------------------------
# Builder stage
# --------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /build

# System deps for OCR / OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
      libglib2.0-0 \
      libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -U pip setuptools wheel && \
    python -m pip install -r requirements.txt

COPY app ./app
COPY tests ./tests

# ---- RUN TESTS (CI GATE) ----
RUN pytest -q

# --------------------------
# Runtime stage
# --------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=true

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
      libglib2.0-0 \
      libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy app only (NO tests in runtime image)
COPY app ./app
COPY README.md ./README.md

RUN mkdir -p /app/data/uploads && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

ENV UVICORN_WORKERS=1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS}"]