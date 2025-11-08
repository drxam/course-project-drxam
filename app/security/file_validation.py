"""Валидация файлов и защита от path traversal."""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

# Magic bytes для различных типов файлов
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": "image/png",
    b"%PDF": "application/pdf",
    # Для текстовых файлов проверяем первые несколько байтов
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
    "text/plain",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def detect_file_type(content: bytes) -> Optional[str]:
    """Определить тип файла по magic bytes.

    Args:
        content: Содержимое файла (первые байты)

    Returns:
        MIME тип или None если не определён
    """
    for magic, mime_type in MAGIC_BYTES.items():
        if content.startswith(magic):
            return mime_type

    # Проверка на текстовый файл (первые 512 байт должны быть ASCII)
    try:
        content[:512].decode("utf-8")
        return "text/plain"
    except UnicodeDecodeError:
        pass

    return None


def validate_file_size(file_size: int) -> Tuple[bool, Optional[str]]:
    """Проверить размер файла.

    Returns:
        (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
    return True, None


def validate_file_content(
    content: bytes, declared_mime_type: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Проверить содержимое файла по magic bytes.

    Args:
        content: Содержимое файла
        declared_mime_type: Заявленный MIME тип из заголовка

    Returns:
        (is_valid, detected_mime_type, error_message)
    """
    if len(content) == 0:
        return False, None, "File is empty"

    detected_type = detect_file_type(content)

    if detected_type is None:
        return False, None, "Unknown file type or invalid content"

    # Проверка соответствия заявленному типу
    if declared_mime_type:
        if detected_type != declared_mime_type:
            return (
                False,
                detected_type,
                f"MIME type mismatch: declared {declared_mime_type}, detected {detected_type}",
            )

    # Проверка на разрешённый тип
    if detected_type not in ALLOWED_MIME_TYPES:
        return (
            False,
            detected_type,
            f"File type {detected_type} is not allowed",
        )

    return True, detected_type, None


def sanitize_filename(filename: str) -> str:
    """Очистить имя файла от опасных символов.

    Args:
        filename: Оригинальное имя файла

    Returns:
        Очищенное имя файла
    """
    # Удаляем путь, оставляем только имя
    filename = os.path.basename(filename)
    # Удаляем опасные символы
    dangerous_chars = ["/", "\\", "..", "\x00"]
    for char in dangerous_chars:
        filename = filename.replace(char, "")
    return filename


def generate_safe_filename(original_filename: Optional[str] = None) -> str:
    """Сгенерировать безопасное UUID имя файла.

    Args:
        original_filename: Оригинальное имя (для определения расширения)

    Returns:
        UUID имя файла с сохранением расширения (если возможно)
    """
    file_id = str(uuid.uuid4())

    if original_filename:
        # Сохраняем расширение если оно есть
        ext = Path(original_filename).suffix
        if ext and len(ext) <= 10:  # Ограничение на длину расширения
            return f"{file_id}{ext}"

    return file_id


def validate_and_sanitize_path(
    file_path: str, upload_directory: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Проверить и нормализовать путь файла для предотвращения path traversal.

    Args:
        file_path: Путь файла
        upload_directory: Разрешённая директория для загрузки

    Returns:
        (is_valid, normalized_path, error_message)
    """
    # Нормализация пути
    normalized = os.path.normpath(file_path)

    # Абсолютный путь для upload_directory
    upload_dir_abs = os.path.abspath(upload_directory)

    # Абсолютный путь для файла
    file_abs = os.path.abspath(os.path.join(upload_dir_abs, normalized))

    # Проверка, что файл находится внутри upload_directory
    try:
        # os.path.commonpath доступен в Python 3.5+
        common_path = os.path.commonpath([upload_dir_abs, file_abs])
        if common_path != upload_dir_abs:
            return False, None, "Path traversal detected: file outside upload directory"
    except ValueError:
        # Пути на разных дисках (Windows)
        return False, None, "Invalid path"

    # Проверка на симлинки
    if os.path.islink(file_abs):
        return False, None, "Symbolic links are not allowed"

    return True, file_abs, None
