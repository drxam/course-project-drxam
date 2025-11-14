"""Валидация входных данных для защиты от уязвимостей secure coding."""

import asyncio
from typing import Optional, Tuple

# Безопасные диапазоны для integer значений
MIN_INT_VALUE = -(2**31)  # -2147483648
MAX_INT_VALUE = 2**31 - 1  # 2147483647

# Максимальная длина строки
MAX_STRING_LENGTH = 10000

# Максимальное время выполнения операции (в секундах)
DEFAULT_TIMEOUT = 30.0


def validate_integer_range(
    value: int, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """Проверить integer значение на переполнение и допустимый диапазон.

    Args:
        value: Проверяемое значение
        min_value: Минимальное допустимое значение (по умолчанию MIN_INT_VALUE)
        max_value: Максимальное допустимое значение (по умолчанию MAX_INT_VALUE)

    Returns:
        (is_valid, error_message)
    """
    min_val = min_value if min_value is not None else MIN_INT_VALUE
    max_val = max_value if max_value is not None else MAX_INT_VALUE

    # Проверка на переполнение Python int (в Python 3 int не имеет ограничений,
    # но мы ограничиваем для совместимости с другими системами)
    if value < min_val:
        return False, f"Integer value {value} is below minimum {min_val} (underflow)"
    if value > max_val:
        return False, f"Integer value {value} exceeds maximum {max_val} (overflow)"

    return True, None


def validate_string_length(
    value: str, max_length: Optional[int] = None, min_length: int = 0
) -> Tuple[bool, Optional[str]]:
    """Проверить длину строки.

    Args:
        value: Проверяемая строка
        max_length: Максимальная длина (по умолчанию MAX_STRING_LENGTH)
        min_length: Минимальная длина

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(value, str):
        return False, "Value must be a string"

    max_len = max_length if max_length is not None else MAX_STRING_LENGTH

    if len(value) < min_length:
        return False, f"String length {len(value)} is below minimum {min_length}"
    if len(value) > max_len:
        return False, f"String length {len(value)} exceeds maximum {max_len}"

    return True, None


def validate_string_format(
    value: str, allowed_chars: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Проверить формат строки на наличие опасных паттернов.

    Args:
        value: Проверяемая строка
        allowed_chars: Дополнительные разрешённые символы
            (не используется, оставлено для совместимости)

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(value, str):
        return False, "Value must be a string"

    # Проверка на опасные паттерны (SQL injection, XSS и т.д.)
    # Проверяем только паттерны, а не каждый символ, чтобы разрешить больше символов
    dangerous_patterns = [
        "<script",  # XSS
        "</script",  # XSS
        "javascript:",  # XSS
        "onerror=",  # XSS
        "onload=",  # XSS
        "';",  # SQL injection
        '";',  # SQL injection
        "--",  # SQL комментарий
        "/*",  # SQL комментарий
        "*/",  # SQL комментарий
        "xp_",  # SQL Server extended procedure
        "sp_",  # SQL Server stored procedure
        "union select",  # SQL injection
        "drop table",  # SQL injection
        "delete from",  # SQL injection
    ]
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if pattern in value_lower:
            return False, f"String contains dangerous pattern: {pattern}"

    # Проверка на отдельные опасные символы в контексте инъекций
    # Разрешаем их только если они не используются в опасных комбинациях
    sql_keywords = ("drop", "delete", "insert")
    if ";" in value and any(keyword in value_lower for keyword in sql_keywords):
        return False, "String contains dangerous pattern: semicolon with SQL keywords"

    return True, None


async def with_timeout(
    coro, timeout: float = DEFAULT_TIMEOUT, timeout_message: str = "Operation timed out"
) -> Tuple[bool, any, Optional[str]]:
    """Выполнить асинхронную операцию с таймаутом.

    Args:
        coro: Корутина для выполнения
        timeout: Максимальное время выполнения в секундах
        timeout_message: Сообщение об ошибке при таймауте

    Returns:
        (is_success, result, error_message)
    """
    try:
        result = await asyncio.wait_for(coro, timeout=timeout)
        return True, result, None
    except asyncio.TimeoutError:
        return False, None, timeout_message
    except Exception as e:
        return False, None, f"Operation failed: {str(e)}"
