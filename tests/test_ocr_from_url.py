import pytest
from app.api.v1 import ocr as ocr_module


@pytest.mark.asyncio
async def test_ocr_from_url_ok(client, monkeypatch):
    async def fake_fetch(url, extra_headers=None):
        return b"fake image bytes"

    monkeypatch.setattr(ocr_module, "fetch_image_bytes", fake_fetch)

    r = client.post(
        "/v1/ocr/from-url",
        json={"image_url": "https://example.com/test.png"},
    )

    assert r.status_code == 200
    body = r.json()

    assert body["ok"] is True
    assert body["data"]["text"] == "FAKE OCR TEXT"