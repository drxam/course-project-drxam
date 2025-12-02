import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile

# Импорт роутеров API v1
from app.api.v1 import auth, items
from app.security.file_validation import (
    generate_safe_filename,
    validate_and_sanitize_path,
    validate_file_content,
    validate_file_size,
)
from app.security.input_validation import (
    validate_integer_range,
    validate_string_format,
    validate_string_length,
    with_timeout,
)
from app.security.problems import create_problem_detail
from app.security.secrets import mask_secrets_in_string

# Настройка логирования с маскированием секретов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="SecDev Course App", version="0.1.0")

# Подключение роутеров API v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware для добавления correlation_id в запросы."""
    import uuid

    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    return response


# Проверка обязательных секретов при запуске (опционально для демо)
# В реальном проекте здесь будет проверка критичных секретов
# try:
#     require_secret("DATABASE_URL")
# except ValueError as e:
#     logger.warning(f"Secret validation: {e}")


class ApiError(Exception):
    """Исключение для API ошибок с RFC 7807 форматом."""

    def __init__(
        self,
        title: str,
        detail: str,
        status: int = 400,
        type_uri: str = None,
        errors: list = None,
    ):
        self.title = title
        self.detail = detail
        self.status = status
        self.type_uri = type_uri
        self.errors = errors or []


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    correlation_id = getattr(request.state, "correlation_id", None)

    # Маскирование секретов в деталях перед логированием
    safe_detail = mask_secrets_in_string(exc.detail)
    logger.error(
        f"API Error [{correlation_id}]: {exc.title} - {safe_detail}",
        extra={"correlation_id": correlation_id},
    )

    # Определяем нужно ли маскировать детали (production режим)
    mask_detail = os.getenv("ENVIRONMENT", "development") == "production"

    return create_problem_detail(
        request=request,
        status=exc.status,
        title=exc.title,
        detail=exc.detail,
        type_uri=exc.type_uri,
        errors=exc.errors if exc.errors else None,
        correlation_id=correlation_id,
        mask_detail=mask_detail,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = getattr(request.state, "correlation_id", None)
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"

    # Маскирование секретов перед логированием
    safe_detail = mask_secrets_in_string(detail)
    logger.error(
        f"HTTP Error [{correlation_id}]: {exc.status_code} - {safe_detail}",
        extra={"correlation_id": correlation_id},
    )

    mask_detail = os.getenv("ENVIRONMENT", "development") == "production"

    return create_problem_detail(
        request=request,
        status=exc.status_code,
        title="HTTP Error",
        detail=detail,
        correlation_id=correlation_id,
        mask_detail=mask_detail,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


def validate_item_name(name: str) -> str:
    """Валидация имени элемента с детальными сообщениями об ошибках"""
    if not name:
        raise ApiError(
            title="Validation Error",
            detail="name is required",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
            errors=[{"field": "name", "message": "name is required"}],
        )

    # Контроль 3: Валидация длины строки
    is_valid_length, length_error = validate_string_length(name, max_length=100, min_length=1)
    if not is_valid_length:
        raise ApiError(
            title="Validation Error",
            detail=length_error or "name length validation failed",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
            errors=[{"field": "name", "message": length_error}],
        )

    # Контроль 3: Валидация формата строки (защита от инъекций)
    is_valid_format, format_error = validate_string_format(name)
    if not is_valid_format:
        raise ApiError(
            title="Validation Error",
            detail=format_error or "name format validation failed",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
            errors=[{"field": "name", "message": format_error}],
        )

    if len(name.strip()) == 0:
        raise ApiError(
            title="Validation Error",
            detail="name cannot be empty or whitespace only",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
            errors=[{"field": "name", "message": "name cannot be empty or whitespace only"}],
        )
    return name.strip()


@app.post("/items")
def create_item(name: str):
    # Используем функцию валидации для переиспользования
    validated_name = validate_item_name(name)

    item = {"id": len(_DB["items"]) + 1, "name": validated_name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    # Контроль 1: Валидация integer параметра (защита от overflow/underflow)
    is_valid, error_msg = validate_integer_range(item_id, min_value=1)
    if not is_valid:
        raise ApiError(
            title="Validation Error",
            detail=error_msg or "Invalid item_id",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
        )

    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(
        title="Not Found",
        detail="item not found",
        status=404,
        type_uri="https://api.example.com/problems/not-found",
    )


# Эндпойнт загрузки файлов с валидацией
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Загрузить файл с валидацией безопасности."""
    correlation_id = getattr(request.state, "correlation_id", None)

    try:
        # Чтение содержимого файла
        contents = await file.read()
        file_size = len(contents)

        # Валидация размера
        is_valid_size, size_error = validate_file_size(file_size)
        if not is_valid_size:
            raise ApiError(
                title="File Size Error",
                detail=size_error,
                status=413,
                type_uri="https://api.example.com/problems/file-too-large",
            )

        # Валидация содержимого
        declared_mime = file.content_type
        is_valid_content, detected_mime, content_error = validate_file_content(
            contents, declared_mime
        )
        if not is_valid_content:
            raise ApiError(
                title="File Validation Error",
                detail=content_error,
                status=422,
                type_uri="https://api.example.com/problems/invalid-file",
            )

        # Генерация безопасного имени файла
        safe_filename = generate_safe_filename(file.filename)

        # Валидация и нормализация пути
        is_valid_path, file_path, path_error = validate_and_sanitize_path(
            safe_filename, str(UPLOAD_DIR)
        )
        if not is_valid_path:
            raise ApiError(
                title="Path Validation Error",
                detail=path_error,
                status=422,
                type_uri="https://api.example.com/problems/path-traversal",
            )

        # Сохранение файла
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(
            f"File uploaded successfully [{correlation_id}]: {safe_filename} "
            f"({detected_mime}, {file_size} bytes)",
            extra={"correlation_id": correlation_id},
        )

        return {
            "filename": safe_filename,
            "original_filename": file.filename,
            "mime_type": detected_mime,
            "size": file_size,
            "correlation_id": correlation_id,
        }

    except ApiError:
        raise
    except Exception:
        logger.exception(f"Unexpected error during file upload [{correlation_id}]")
        raise ApiError(
            title="Upload Error",
            detail="An error occurred during file upload",
            status=500,
            type_uri="https://api.example.com/problems/internal-error",
        )


# Эндпойнт для демонстрации контроля таймаутов
@app.post("/process")
async def process_data(request: Request, delay: float = 1.0):
    """Обработать данные с таймаутом (контроль 2)."""
    correlation_id = getattr(request.state, "correlation_id", None)

    # Валидация параметра delay
    if delay < 0 or delay > 60:
        raise ApiError(
            title="Validation Error",
            detail="delay must be between 0 and 60 seconds",
            status=422,
            type_uri="https://api.example.com/problems/validation-error",
        )

    async def process_operation():
        """Имитация долгой операции."""
        import asyncio

        await asyncio.sleep(delay)
        return {"processed": True, "delay": delay}

    # Контроль 2: Таймаут для операции
    is_success, result, error_msg = await with_timeout(
        process_operation(),
        timeout=5.0,
        timeout_message="Operation exceeded 5 second timeout",
    )

    if not is_success:
        raise ApiError(
            title="Timeout Error",
            detail=error_msg or "Operation timed out",
            status=408,
            type_uri="https://api.example.com/problems/timeout",
        )

    return {"result": result, "correlation_id": correlation_id}
