"""RFC 7807 Problem Details для обработки ошибок."""

import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


def create_problem_detail(
    request: Request,
    status: int,
    title: str,
    detail: str,
    type_uri: Optional[str] = None,
    errors: Optional[list] = None,
    correlation_id: Optional[str] = None,
    mask_detail: bool = False,
) -> JSONResponse:
    """Создать RFC 7807 Problem Detail ответ.

    Args:
        request: FastAPI Request объект
        status: HTTP статус код
        title: Краткое описание проблемы
        detail: Детальное сообщение
        type_uri: URI типа ошибки (опционально)
        errors: Массив ошибок валидации (опционально)
        correlation_id: ID для связи с логами (генерируется если не указан)
        mask_detail: Маскировать детали для production

    Returns:
        JSONResponse с RFC 7807 форматом
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    # Маскирование деталей для production
    if mask_detail:
        # В production показываем обобщённое сообщение
        if status == 422:
            detail = "Validation failed. Check request parameters."
        elif status == 404:
            detail = "Resource not found."
        elif status == 500:
            detail = "Internal server error."
        else:
            detail = "An error occurred."

    # Базовый тип ошибки
    if type_uri is None:
        type_uri = f"https://api.example.com/problems/{status // 100}xx"

    problem: Dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url),
        "correlation_id": correlation_id,
    }

    if errors:
        problem["errors"] = errors

    return JSONResponse(
        status_code=status,
        content=problem,
        headers={"Content-Type": "application/problem+json"},
    )
