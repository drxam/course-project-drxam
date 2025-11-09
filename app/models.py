"""Модели данных для приложения."""

from typing import Optional


class User:
    """Модель пользователя."""

    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        hashed_password: str,
        role: str = "user",
    ):
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.role = role

    def to_dict(self) -> dict:
        """Преобразовать в словарь (без пароля)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
        }


class Item:
    """Модель элемента."""

    def __init__(
        self,
        id: int,
        name: str,
        owner_id: int,
        description: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.description = description

    def to_dict(self) -> dict:
        """Преобразовать в словарь."""
        result = {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
        }
        if self.description:
            result["description"] = self.description
        return result
