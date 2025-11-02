"""Управление секретами и маскирование в логах."""

import os
import re
from typing import Optional

# Паттерны для поиска секретов в строках
SECRET_PATTERNS = [
    (r"(?i)(password\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(token\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(api[_-]?key\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(secret\s*[=:]\s*)([^\s&\"']+)", r"\1***MASKED***"),
    (r"(?i)(authorization\s*:\s*Bearer\s+)([^\s\"']+)", r"\1***MASKED***"),
    (r"(?i)(authorization\s*:\s*)([^\s\"']+)", r"\1***MASKED***"),
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
    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result
