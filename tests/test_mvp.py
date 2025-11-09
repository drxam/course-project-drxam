"""Тесты для MVP функционала (аутентификация, CRUD, роли)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_user():
    """Тест: регистрация нового пользователя."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_username():
    """Негативный тест: регистрация с существующим username."""
    # Первая регистрация
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate1@example.com",
            "password": "securepassword123",
        },
    )
    # Попытка зарегистрироваться с тем же username
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "duplicate2@example.com",
            "password": "securepassword123",
        },
    )
    assert r.status_code == 409
    assert "already registered" in r.json()["detail"].lower()


def test_register_short_password():
    """Негативный тест: регистрация с коротким паролем (< 12 символов)."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "shortpass",
            "email": "short@example.com",
            "password": "short123",
        },
    )
    assert r.status_code == 422
    assert "12" in r.json()["detail"].lower() or "length" in r.json()["detail"].lower()


def test_login():
    """Тест: вход пользователя."""
    # Сначала регистрируем
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "securepassword123",
        },
    )
    # Затем входим
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "loginuser", "password": "securepassword123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password():
    """Негативный тест: вход с неверным паролем."""
    # Регистрируем
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "securepassword123",
        },
    )
    # Пытаемся войти с неверным паролем
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "wrongpass", "password": "wrongpassword"},
    )
    assert r.status_code == 401


def test_logout():
    """Тест: выход пользователя."""
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    assert "message" in r.json()


def test_create_item():
    """Тест: создание item с аутентификацией."""
    # Регистрируем и получаем токен
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "itemcreator",
            "email": "item@example.com",
            "password": "securepassword123",
        },
    )
    token = r.json()["access_token"]

    # Создаём item
    r = client.post(
        "/api/v1/items",
        json={"name": "Test Item", "description": "Test description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Test Item"
    assert "owner_id" in body
    assert body["owner_id"] > 0


def test_create_item_unauthorized():
    """Негативный тест: создание item без токена."""
    r = client.post(
        "/api/v1/items",
        json={"name": "Test Item"},
    )
    assert r.status_code == 403


def test_get_item():
    """Тест: получение item по ID."""
    # Регистрируем
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "getitemuser",
            "email": "getitem@example.com",
            "password": "securepassword123",
        },
    )
    token = r.json()["access_token"]

    # Создаём item
    r = client.post(
        "/api/v1/items",
        json={"name": "My Item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = r.json()["id"]

    # Получаем item
    r = client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == item_id
    assert r.json()["name"] == "My Item"


def test_get_item_unauthorized():
    """Негативный тест: получение item без токена."""
    r = client.get("/api/v1/items/1")
    assert r.status_code == 403


def test_get_item_other_user():
    """Негативный тест: получение чужого item."""
    # Пользователь 1 создаёт item
    r1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "securepassword123",
        },
    )
    token1 = r1.json()["access_token"]

    r = client.post(
        "/api/v1/items",
        json={"name": "User1 Item"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    item_id = r.json()["id"]

    # Пользователь 2 пытается получить item пользователя 1
    r2 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "securepassword123",
        },
    )
    token2 = r2.json()["access_token"]

    r = client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r.status_code == 403


def test_list_items():
    """Тест: получение списка items с пагинацией."""
    # Регистрируем
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "listuser",
            "email": "list@example.com",
            "password": "securepassword123",
        },
    )
    token = r.json()["access_token"]

    # Создаём несколько items
    for i in range(3):
        client.post(
            "/api/v1/items",
            json={"name": f"Item {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Получаем список
    r = client.get(
        "/api/v1/items?limit=10&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) == 3


def test_update_item():
    """Тест: обновление item."""
    # Регистрируем
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "updateuser",
            "email": "update@example.com",
            "password": "securepassword123",
        },
    )
    token = r.json()["access_token"]

    # Создаём item
    r = client.post(
        "/api/v1/items",
        json={"name": "Original Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = r.json()["id"]

    # Обновляем
    r = client.patch(
        f"/api/v1/items/{item_id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


def test_update_item_other_user():
    """Негативный тест: обновление чужого item."""
    # Пользователь 1
    r1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "updater1",
            "email": "updater1@example.com",
            "password": "securepassword123",
        },
    )
    token1 = r1.json()["access_token"]

    r = client.post(
        "/api/v1/items",
        json={"name": "User1 Item"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    item_id = r.json()["id"]

    # Пользователь 2 пытается обновить
    r2 = client.post(
        "/api/v1/auth/register",
        json={
            "username": "updater2",
            "email": "updater2@example.com",
            "password": "securepassword123",
        },
    )
    token2 = r2.json()["access_token"]

    r = client.patch(
        f"/api/v1/items/{item_id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r.status_code == 403


def test_delete_item():
    """Тест: удаление item."""
    # Регистрируем
    r = client.post(
        "/api/v1/auth/register",
        json={
            "username": "deleteuser",
            "email": "delete@example.com",
            "password": "securepassword123",
        },
    )
    token = r.json()["access_token"]

    # Создаём item
    r = client.post(
        "/api/v1/items",
        json={"name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = r.json()["id"]

    # Удаляем
    r = client.delete(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    # Проверяем что удалён
    r = client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
