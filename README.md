# kennedycore-svc-ocr

Generic, production-ready OCR microservice for extracting text and layout from images.

This service is part of the **KennedyCore** ecosystem and is designed as a **reusable core component**.
It focuses exclusively on OCR capabilities and intentionally avoids any business-specific logic.

---

## 🧰 Tech stack

- **FastAPI** (HTTP API)
- **Uvicorn** (ASGI server)
- **PaddleOCR / PaddlePaddle** (OCR engine)
- **OpenCV** (image decode + preprocessing)
- **httpx** (safe streaming downloads for URL-based OCR)

---

## ✨ Features

- OCR extraction from images using PaddleOCR
- Image upload and image URL processing
- Bounding boxes and confidence scores per text block
- Optional image preprocessing (padding + smart resize)
- RFC 7807 compliant error responses (`application/problem+json`)
- TraceId support via `X-Request-Id`
- Stateless and reusable by design

---

## 🐍 Python version

This service requires **Python 3.12**.

> ⚠️ Python 3.13+ is **not supported** due to PaddleOCR / PaddlePaddle dependencies.

---

## ⚙️ Configuration

This project reads settings from environment variables.

- Do **not** commit `.env`

Key variables:

- `OCR_LANG` (default: `es`)
- `OCR_DROP_SCORE` (default: `0.30`)
- `MAX_FILE_MB` (default: `10`)
- `ALLOWED_EXT` (default: `.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff`)
- `PROBLEM_BASE_URL` (RFC7807 `type` base URI)

---

## 🚀 Setup (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

---

## ▶️ Run the service

```powershell
uvicorn app.main:app --reload --port 8000
```

The service will be available at:

- API base: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`
- Healthcheck: `http://localhost:8000/health`

---

## 🐳 Docker

```bash
docker build -t kennedycore/ocr:local .
docker run -p 8000:8000 kennedycore/ocr:local
```

---

## 🧩 Docker Compose

```bash
docker compose up -d --build
```

---

## 🧪 Usage

### OCR from file upload

```powershell
curl -X POST "http://localhost:8000/v1/ocr" `
  -F "file=@test.jpg"
```

### OCR from image URL

```powershell
curl -X POST "http://localhost:8000/v1/ocr/from-url" `
  -H "Content-Type: application/json" `
  -d "{`"image_url`":`"https://example.com/image.png`"}"
```

### OCR from image URL with custom headers

Useful for sites that block direct downloads.

```powershell
curl -X POST "http://localhost:8000/v1/ocr/from-url" `
  -H "Content-Type: application/json" `
  -d "{`"image_url`":`"https://site.com/image.png`",`"headers`":{`"Referer`":`"https://site.com`"}}"
```

---

## 📦 Response format

```json
{
  "ok": true,
  "traceId": "uuid",
  "data": {
    "text": "Detected text",
    "blocks": [
      {
        "text": "Detected block",
        "confidence": 0.98,
        "box": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
      }
    ],
    "preprocess": {}
  }
}
```

Errors are returned using **RFC 7807 – Problem Details for HTTP APIs** (`application/problem+json`).

---

## 🔐 Security notes

- URL-based OCR performs **streaming downloads** and enforces a **max size limit**.
- Basic SSRF protections are included (private/loopback networks blocked by default).

---

## 📈 Performance notes

- OCR is CPU-bound; calls run in a threadpool to avoid blocking the FastAPI event loop.
- The engine uses a lock to remain safe if the underlying OCR is not thread-safe.

---

## 🧱 Design principles

- Single responsibility (OCR only)
- No business logic
- Deterministic and stateless
- Ready for CI/CD pipelines
- Suitable for internal platforms and microservice architectures

---

## 📄 License

MIT
