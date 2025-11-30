"""Эндпойнты для работы с items."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.database import create_item, delete_item, get_item_by_id, get_items, update_item
from app.dependencies import get_current_active_user
from app.models import Item, User
from app.security.input_validation import (
    validate_integer_range,
    validate_string_format,
    validate_string_length,
)

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    """Модель для создания item."""

    name: str
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    """Модель для обновления item."""

    name: Optional[str] = None
    description: Optional[str] = None


class ItemResponse(BaseModel):
    """Модель ответа item."""

    id: int
    name: str
    owner_id: int
    description: Optional[str] = None


def check_item_ownership(item: Item, user: User) -> bool:
    """Проверить владение элементом."""
    return item.owner_id == user.id or user.role == "admin"


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item_endpoint(
    request: Request,
    item_data: ItemCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Создать новый item."""
    getattr(request.state, "correlation_id", None)

    # Валидация name
    is_valid_length, length_error = validate_string_length(
        item_data.name, max_length=100, min_length=1
    )
    if not is_valid_length:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=length_error or "Invalid name length",
        )

    is_valid_format, format_error = validate_string_format(item_data.name)
    if not is_valid_format:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=format_error or "Invalid name format",
        )

    # Валидация description если есть
    if item_data.description:
        is_valid_length, length_error = validate_string_length(
            item_data.description, max_length=500, min_length=1
        )
        if not is_valid_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=length_error or "Invalid description length",
            )

    item = create_item(
        name=item_data.name,
        owner_id=current_user.id,
        description=item_data.description,
    )

    return ItemResponse(**item.to_dict())


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item_endpoint(
    request: Request,
    item_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Получить item по ID."""
    getattr(request.state, "correlation_id", None)

    # Валидация item_id
    is_valid, error_msg = validate_integer_range(item_id, min_value=1)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Invalid item_id",
        )

    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Проверка доступа (только владелец или admin)
    if not check_item_ownership(item, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this item",
        )

    return ItemResponse(**item.to_dict())


@router.get("", response_model=List[ItemResponse])
async def list_items(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """Получить список items с пагинацией."""
    getattr(request.state, "correlation_id", None)

    # Валидация параметров пагинации
    is_valid_limit, _ = validate_integer_range(limit, min_value=1, max_value=100)
    if not is_valid_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit must be between 1 and 100",
        )

    is_valid_offset, _ = validate_integer_range(offset, min_value=0)
    if not is_valid_offset:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="offset must be >= 0",
        )

    # Получаем только items текущего пользователя (или все для admin)
    owner_id = None if current_user.role == "admin" else current_user.id
    items = get_items(owner_id=owner_id, limit=limit, offset=offset)

    return [ItemResponse(**item.to_dict()) for item in items]


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item_endpoint(
    request: Request,
    item_id: int,
    item_data: ItemUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """Обновить item."""
    getattr(request.state, "correlation_id", None)

    # Валидация item_id
    is_valid, error_msg = validate_integer_range(item_id, min_value=1)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Invalid item_id",
        )

    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Проверка доступа
    if not check_item_ownership(item, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this item",
        )

    # Валидация полей если они обновляются
    if item_data.name is not None:
        is_valid_length, length_error = validate_string_length(
            item_data.name, max_length=100, min_length=1
        )
        if not is_valid_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=length_error or "Invalid name length",
            )

        is_valid_format, format_error = validate_string_format(item_data.name)
        if not is_valid_format:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=format_error or "Invalid name format",
            )

    if item_data.description is not None:
        is_valid_length, length_error = validate_string_length(
            item_data.description, max_length=500, min_length=1
        )
        if not is_valid_length:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=length_error or "Invalid description length",
            )

    updated_item = update_item(
        item_id=item_id,
        name=item_data.name,
        description=item_data.description,
    )

    return ItemResponse(**updated_item.to_dict())


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_endpoint(
    request: Request,
    item_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """Удалить item."""
    getattr(request.state, "correlation_id", None)

    # Валидация item_id
    is_valid, error_msg = validate_integer_range(item_id, min_value=1)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg or "Invalid item_id",
        )

    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    # Проверка доступа
    if not check_item_ownership(item, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this item",
        )

    delete_item(item_id)
    return None
