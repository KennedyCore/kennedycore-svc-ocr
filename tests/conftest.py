# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeOcrEngine:
    def extract_from_bytes(self, data: bytes, *, preprocess: bool, return_blocks: bool):
        return {
            "text": "FAKE OCR TEXT",
            "blocks": [
                {
                    "text": "FAKE",
                    "confidence": 0.99,
                    "box": [[0, 0], [10, 0], [10, 10], [0, 10]],
                }
            ],
            "preprocess": {"mock": True},
        }


@pytest.fixture(scope="session")
def client():

    app.state.ocr_engine = FakeOcrEngine()
    return TestClient(app)