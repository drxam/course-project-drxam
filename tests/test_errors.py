"""Тесты для обработки ошибок в формате RFC 7807."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    """Тест: ошибка 404 в формате RFC 7807."""
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()
    # Проверяем RFC 7807 формат
    assert "title" in body
    assert "detail" in body
    assert "status" in body
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert "correlation_id" in body


def test_validation_error():
    """Тест: ошибка валидации в формате RFC 7807."""
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    # Проверяем RFC 7807 формат
    assert "title" in body
    assert body["title"] == "Validation Error"
    assert body["status"] == 422
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0