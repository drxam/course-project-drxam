"""Эндпойнты аутентификации."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from app.database import create_user, get_user_by_email, get_user_by_username
from app.security.auth import Role, create_access_token, get_password_hash, verify_password
from app.security.input_validation import validate_string_length

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""

    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Запрос на вход."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Ответ с токеном."""

    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, user_data: RegisterRequest):
    """Регистрация нового пользователя."""
    getattr(request.state, "correlation_id", None)

    # Валидация username
    is_valid, error_msg = validate_string_length(user_data.username, max_length=50, min_length=3)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Invalid username",
        )

    # Валидация пароля (минимум 12 символов согласно NFR-005)
    is_valid, error_msg = validate_string_length(user_data.password, max_length=128, min_length=12)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Password must be at least 12 characters",
        )

    # Проверка на существующего пользователя
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Создание пользователя
    hashed_password = get_password_hash(user_data.password)
    user = create_user(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=Role.USER,
    )

    # Создание токена (sub должен быть строкой для JWT)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, credentials: LoginRequest):
    """Вход пользователя."""
    getattr(request.state, "correlation_id", None)

    # Поиск пользователя
    user = get_user_by_username(credentials.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверка пароля
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создание токена (sub должен быть строкой для JWT)
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(request: Request):
    """Выход пользователя (в MVP просто подтверждение)."""
    # В реальном приложении здесь была бы инвалидация токена
    # В MVP просто возвращаем успех
    return {"message": "Successfully logged out"}
