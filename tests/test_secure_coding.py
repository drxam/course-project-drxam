"""Тесты для secure coding контролей (P06).

Проверяет:
1. Валидация integer параметров (защита от overflow/underflow)
2. Таймауты для операций
3. Валидация строковых параметров (длина, формат)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ========== Контроль 1: Валидация integer параметров ==========


def test_integer_validation_positive():
    """Тест: успешная валидация валидного integer."""
    # Создаём элемент
    r = client.post("/items", params={"name": "test"})
    assert r.status_code == 200
    item_id = r.json()["id"]

    # Получаем элемент с валидным ID
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 200
    assert r.json()["id"] == item_id


def test_integer_validation_negative_underflow():
    """Негативный тест: integer underflow (отрицательное значение)."""
    r = client.get("/items/-1")
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert (
        "underflow" in body["detail"].lower()
        or "below minimum" in body["detail"].lower()
    )
    assert body["status"] == 422


def test_integer_validation_negative_zero():
    """Негативный тест: integer validation для нуля."""
    r = client.get("/items/0")
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["status"] == 422


def test_integer_validation_negative_overflow():
    """Негативный тест: integer overflow (слишком большое значение)."""
    # Используем значение больше MAX_INT_VALUE (2147483647)
    large_id = 2**31  # 2147483648
    r = client.get(f"/items/{large_id}")
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert (
        "overflow" in body["detail"].lower()
        or "exceeds maximum" in body["detail"].lower()
    )
    assert body["status"] == 422


# ========== Контроль 2: Таймауты для операций ==========


def test_timeout_positive():
    """Тест: успешное выполнение операции в пределах таймаута."""
    r = client.post("/process", params={"delay": 1.0})
    assert r.status_code == 200
    body = r.json()
    assert "result" in body
    assert body["result"]["processed"] is True
    assert "correlation_id" in body


def test_timeout_negative_exceeded():
    """Негативный тест: операция превышает таймаут."""
    # Запрашиваем задержку 10 секунд, но таймаут 5 секунд
    r = client.post("/process", params={"delay": 10.0})
    assert r.status_code == 408
    body = r.json()
    assert body["title"] == "Timeout Error"
    assert "timeout" in body["detail"].lower()
    assert body["status"] == 408


def test_timeout_negative_invalid_delay():
    """Негативный тест: невалидный параметр delay (отрицательный)."""
    r = client.post("/process", params={"delay": -1.0})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert "delay" in body["detail"].lower()
    assert body["status"] == 422


def test_timeout_negative_too_large_delay():
    """Негативный тест: невалидный параметр delay (слишком большой)."""
    r = client.post("/process", params={"delay": 100.0})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert "delay" in body["detail"].lower()
    assert body["status"] == 422


# ========== Контроль 3: Валидация строковых параметров ==========


def test_string_validation_positive():
    """Тест: успешная валидация валидной строки."""
    r = client.post("/items", params={"name": "valid-item-name"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "valid-item-name"


def test_string_validation_negative_too_long():
    """Негативный тест: строка превышает максимальную длину."""
    # Создаём строку длиннее 100 символов
    long_name = "a" * 101
    r = client.post("/items", params={"name": long_name})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert (
        "exceeds maximum" in body["detail"].lower()
        or "length" in body["detail"].lower()
    )
    assert body["status"] == 422


def test_string_validation_negative_empty():
    """Негативный тест: пустая строка."""
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["status"] == 422


def test_string_validation_negative_sql_injection():
    """Негативный тест: попытка SQL инъекции в строке."""
    # Попытка SQL инъекции
    sql_injection = "test'; DROP TABLE items; --"
    r = client.post("/items", params={"name": sql_injection})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert (
        "dangerous" in body["detail"].lower() or "disallowed" in body["detail"].lower()
    )
    assert body["status"] == 422


def test_string_validation_negative_xss_attempt():
    """Негативный тест: попытка XSS инъекции в строке."""
    # Попытка XSS
    xss_attempt = "<script>alert('xss')</script>"
    r = client.post("/items", params={"name": xss_attempt})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert (
        "dangerous" in body["detail"].lower() or "disallowed" in body["detail"].lower()
    )
    assert body["status"] == 422


def test_string_validation_negative_semicolon_with_sql():
    """Негативный тест: строка с точкой с запятой и SQL ключевым словом."""
    r = client.post("/items", params={"name": "test;drop table"})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["status"] == 422


def test_string_validation_negative_sql_comment():
    """Негативный тест: строка с SQL комментарием."""
    r = client.post("/items", params={"name": "test--comment"})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["status"] == 422


def test_string_validation_negative_sql_block_comment():
    """Негативный тест: строка с SQL блочным комментарием."""
    r = client.post("/items", params={"name": "test/*comment*/"})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["status"] == 422
