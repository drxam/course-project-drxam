"""Управление секретами и маскирование в логах."""

import os
import re
from typing import Optional

# Паттерны для поиска секретов в строках
# Порядок важен: более специфичные паттерны должны быть первыми
SECRET_PATTERNS = [
    # Bearer токены (самый специфичный - должен быть первым)
    (r"(?i)(authorization\s*:\s*Bearer\s+)([^\s\"']+)", r"\1***MASKED***"),
    # Другие типы authorization (Basic, Digest) -
    # пропускается в функции если Bearer уже замаскирован
    (
        r"(?i)(authorization\s*:\s*)([^\s\"']+)",
        r"\1***MASKED***",
    ),
    (r"(?i)(password\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(token\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(api[_-]?key\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(secret\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
]


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Получить секрет из переменных окружения."""
    return os.getenv(key, default)


def require_secret(key: str) -> str:
    """Получить обязательный секрет из переменных окружения.

    Raises:
        ValueError: Если секрет не найден.
    """
    value = os.getenv(key)
    if value is None or value == "":
        raise ValueError(f"Required secret '{key}' is not set in environment variables")
    return value


def mask_secrets_in_string(text: str) -> str:
    """Маскировать секреты в строке для безопасного логирования.

    Args:
        text: Строка для маскирования

    Returns:
        Строка с замаскированными секретами
    """
    result = text
    # Если строка уже содержит замаскированный Bearer токен, пропускаем второй authorization паттерн
    has_bearer_masked = "Bearer ***MASKED***" in result

    for i, (pattern, replacement) in enumerate(SECRET_PATTERNS):
        # Пропускаем второй паттерн (индекс 1) если уже есть замаскированный Bearer
        if i == 1 and has_bearer_masked:
            continue
        result = re.sub(pattern, replacement, result)
        # Обновляем флаг после применения первого паттерна
        if i == 0 and "Bearer ***MASKED***" in result:
            has_bearer_masked = True

    return result
