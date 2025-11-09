"""Простое in-memory хранилище данных (для MVP)."""

from typing import Dict, List, Optional

from app.models import Item, User

# In-memory база данных
_users_db: Dict[int, User] = {}
_items_db: Dict[int, Item] = {}
_user_id_counter = 1
_item_id_counter = 1


def get_user_by_id(user_id: int) -> Optional[User]:
    """Получить пользователя по ID."""
    return _users_db.get(user_id)


def get_user_by_username(username: str) -> Optional[User]:
    """Получить пользователя по username."""
    for user in _users_db.values():
        if user.username == username:
            return user
    return None


def get_user_by_email(email: str) -> Optional[User]:
    """Получить пользователя по email."""
    for user in _users_db.values():
        if user.email == email:
            return user
    return None


def create_user(
    username: str, email: str, hashed_password: str, role: str = "user"
) -> User:
    """Создать нового пользователя."""
    global _user_id_counter
    user_id = _user_id_counter
    _user_id_counter += 1
    user = User(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
    )
    _users_db[user_id] = user
    return user


def get_item_by_id(item_id: int) -> Optional[Item]:
    """Получить элемент по ID."""
    return _items_db.get(item_id)


def get_items(
    owner_id: Optional[int] = None, limit: int = 10, offset: int = 0
) -> List[Item]:
    """Получить список элементов с пагинацией."""
    items = list(_items_db.values())

    # Фильтр по владельцу
    if owner_id is not None:
        items = [item for item in items if item.owner_id == owner_id]

    # Пагинация
    return items[offset : offset + limit]


def create_item(name: str, owner_id: int, description: Optional[str] = None) -> Item:
    """Создать новый элемент."""
    global _item_id_counter
    item_id = _item_id_counter
    _item_id_counter += 1
    item = Item(id=item_id, name=name, owner_id=owner_id, description=description)
    _items_db[item_id] = item
    return item


def update_item(
    item_id: int, name: Optional[str] = None, description: Optional[str] = None
) -> Optional[Item]:
    """Обновить элемент."""
    item = _items_db.get(item_id)
    if not item:
        return None
    if name is not None:
        item.name = name
    if description is not None:
        item.description = description
    return item


def delete_item(item_id: int) -> bool:
    """Удалить элемент."""
    if item_id in _items_db:
        del _items_db[item_id]
        return True
    return False
