"""Тесты для загрузки файлов с валидацией."""

import os
from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_jpeg_file(size: int = 1000):
    """Создать валидный JPEG файл."""
    # JPEG magic bytes: FF D8 FF
    jpeg_start = b"\xff\xd8\xff\xe0"
    jpeg_end = b"\xff\xd9"
    content = jpeg_start + b"x" * (size - len(jpeg_start) - len(jpeg_end)) + jpeg_end
    return content, "image/jpeg"


def create_png_file(size: int = 1000):
    """Создать валидный PNG файл."""
    # PNG magic bytes
    png_start = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"
    content = png_start + b"x" * (size - len(png_start))
    return content, "image/png"


def create_text_file(content: str = "Hello, World!"):
    """Создать текстовый файл."""
    return content.encode("utf-8"), "text/plain"


def test_upload_valid_jpeg():
    """Тест: успешная загрузка валидного JPEG файла."""
    content, mime_type = create_jpeg_file(5000)

    files = {"file": ("test.jpg", BytesIO(content), mime_type)}
    r = client.post("/upload", files=files)

    assert r.status_code == 200
    body = r.json()
    assert "filename" in body
    assert body["mime_type"] == "image/jpeg"
    assert body["size"] == len(content)
    assert "correlation_id" in body

    # Проверяем, что файл сохранён
    assert os.path.exists(f"uploads/{body['filename']}")


def test_upload_file_too_large():
    """Тест: отклонение файла превышающего максимальный размер."""
    # Создаём файл больше 10MB
    content, mime_type = create_jpeg_file(11 * 1024 * 1024)

    files = {"file": ("large.jpg", BytesIO(content), mime_type)}
    r = client.post("/upload", files=files)

    assert r.status_code == 413
    body = r.json()
    assert body["title"] == "File Size Error"
    assert "exceeds maximum" in body["detail"].lower()
    assert body["status"] == 413


def test_upload_invalid_magic_bytes():
    """Тест: отклонение файла с неверными magic bytes."""
    # Создаём файл с расширением .jpg, но с PNG magic bytes
    png_content, _ = create_png_file(1000)

    files = {"file": ("fake.jpg", BytesIO(png_content), "image/jpeg")}
    r = client.post("/upload", files=files)

    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "File Validation Error"
    assert "mime type mismatch" in body["detail"].lower() or "not allowed" in body["detail"].lower()


def test_upload_unknown_file_type():
    """Тест: отклонение файла неизвестного типа."""
    # Создаём файл с неверными magic bytes (executable-like)
    content = b"MZ\x90\x00" + b"x" * 1000  # PE executable magic bytes

    files = {"file": ("evil.exe", BytesIO(content), "application/octet-stream")}
    r = client.post("/upload", files=files)

    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "File Validation Error"
    assert "unknown file type" in body["detail"].lower() or "not allowed" in body["detail"].lower()


def test_upload_path_traversal_attempt():
    """Тест: отклонение попытки path traversal."""
    content, mime_type = create_jpeg_file(1000)

    # Попытка использовать path traversal в имени файла
    files = {"file": ("../../../etc/passwd.jpg", BytesIO(content), mime_type)}
    r = client.post("/upload", files=files)

    # Файл должен быть отклонён или имя должно быть санитизировано
    # В нашей реализации имя файла генерируется как UUID, поэтому path traversal невозможен
    # Но можно проверить, что система работает корректно
    r = client.post("/upload", files=files)

    # Файл всё равно должен быть отклонён на этапе валидации пути
    # или сохранён с безопасным UUID именем
    assert r.status_code in [200, 422]  # В зависимости от реализации

    if r.status_code == 200:
        # Если успешно, проверяем что файл сохранён с безопасным именем
        body = r.json()
        assert ".." not in body["filename"]
        assert "/" not in body["filename"]
        assert "\\" not in body["filename"]


def test_upload_text_file():
    """Тест: успешная загрузка текстового файла."""
    content, mime_type = create_text_file("Test content")

    files = {"file": ("test.txt", BytesIO(content), mime_type)}
    r = client.post("/upload", files=files)

    assert r.status_code == 200
    body = r.json()
    assert body["mime_type"] == "text/plain"
    assert body["size"] == len(content)


def test_upload_empty_file():
    """Тест: отклонение пустого файла."""
    files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
    r = client.post("/upload", files=files)

    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "File Validation Error"
    assert "empty" in body["detail"].lower()
