from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body and body["error"]["code"] == "not_found"


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"


def test_validation_error_whitespace():
    """Тест для новой валидации - только пробелы"""
    r = client.post("/items", params={"name": "   "})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert "whitespace" in body["error"]["message"]


def test_validation_error_too_long():
    """Тест для валидации длины"""
    long_name = "a" * 101
    r = client.post("/items", params={"name": long_name})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
