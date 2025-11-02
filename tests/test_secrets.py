"""Тесты для маскирования секретов в логах."""

import os

import pytest

from app.security.secrets import get_secret, mask_secrets_in_string, require_secret


def test_mask_password():
    """Тест: маскирование пароля в строке."""
    text = "User logged in with password=secret123"
    masked = mask_secrets_in_string(text)

    assert "password=***MASKED***" in masked
    assert "secret123" not in masked


def test_mask_token():
    """Тест: маскирование токена в строке."""
    text = "Authorization header: token=abc123xyz"
    masked = mask_secrets_in_string(text)

    assert "token=***MASKED***" in masked
    assert "abc123xyz" not in masked


def test_mask_api_key():
    """Тест: маскирование API ключа в строке."""
    text = "API request with api_key=sk_live_1234567890"
    masked = mask_secrets_in_string(text)

    assert "api_key=***MASKED***" in masked
    assert "sk_live_1234567890" not in masked


def test_mask_bearer_token():
    """Тест: маскирование Bearer токена."""
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    masked = mask_secrets_in_string(text)

    assert "Bearer ***MASKED***" in masked
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked


def test_mask_multiple_secrets():
    """Тест: маскирование нескольких секретов в одной строке."""
    text = "password=secret123 and token=abc123 and api_key=xyz789"
    masked = mask_secrets_in_string(text)

    assert "password=***MASKED***" in masked
    assert "token=***MASKED***" in masked
    assert "api_key=***MASKED***" in masked
    assert "secret123" not in masked
    assert "abc123" not in masked
    assert "xyz789" not in masked


def test_no_secrets_no_change():
    """Тест: строка без секретов не изменяется."""
    text = "This is a normal log message without secrets"
    masked = mask_secrets_in_string(text)

    assert masked == text


def test_get_secret_exists():
    """Тест: получение существующего секрета."""
    os.environ["TEST_SECRET"] = "test_value"
    try:
        value = get_secret("TEST_SECRET")
        assert value == "test_value"
    finally:
        os.environ.pop("TEST_SECRET", None)


def test_get_secret_not_exists():
    """Тест: получение несуществующего секрета."""
    value = get_secret("NON_EXISTENT_SECRET")
    assert value is None

    value = get_secret("NON_EXISTENT_SECRET", default="default_value")
    assert value == "default_value"


def test_require_secret_exists():
    """Тест: require_secret для существующего секрета."""
    os.environ["REQUIRED_SECRET"] = "required_value"
    try:
        value = require_secret("REQUIRED_SECRET")
        assert value == "required_value"
    finally:
        os.environ.pop("REQUIRED_SECRET", None)


def test_require_secret_not_exists():
    """Тест: require_secret для несуществующего секрета выбрасывает ошибку."""
    with pytest.raises(ValueError, match="Required secret"):
        require_secret("NON_EXISTENT_REQUIRED_SECRET")
