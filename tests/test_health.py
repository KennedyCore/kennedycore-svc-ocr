from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200

    body = r.json()

    assert body["ok"] is True
    assert "ready" in body

    assert isinstance(body["ready"], bool)