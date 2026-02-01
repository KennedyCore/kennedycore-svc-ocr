import io


def test_ocr_upload_ok(client):
    fake_image = io.BytesIO(b"fake image bytes")

    r = client.post(
        "/v1/ocr",
        files={"file": ("test.png", fake_image, "image/png")},
    )

    assert r.status_code == 200
    body = r.json()

    assert body["ok"] is True
    assert body["data"]["text"] == "FAKE OCR TEXT"
    assert len(body["data"]["blocks"]) == 1


def test_ocr_upload_unsupported_format(client):
    fake_file = io.BytesIO(b"123")

    r = client.post(
        "/v1/ocr",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )

    assert r.status_code == 415