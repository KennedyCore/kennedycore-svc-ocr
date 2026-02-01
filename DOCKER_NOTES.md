# Cómo usar

## Build
docker build -t kennedycore/ocr:local .

## Run
docker run --rm -p 8000:8000       -e UVICORN_WORKERS=1       -e PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=true       -v "%cd%/data/uploads:/app/data/uploads"       kennedycore/ocr:local

## Con docker compose
docker compose up --build

## Test
curl -X POST "http://localhost:8000/v1/ocr" -F "file=@test.jpg"
