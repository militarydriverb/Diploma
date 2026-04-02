from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemRemove, CartItemsAdd, CartResponse
from app.services.cart import (
    add_item_to_cart,
    add_items_to_cart,
    calculate_total,
    clear_cart,
    get_or_create_cart,
    remove_item_from_cart,
)

router = APIRouter(prefix="/cart", tags=["Корзина"])


def _build_cart_response(cart) -> CartResponse:
    """Формирует ответ корзины с вычисленной итоговой стоимостью."""
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=cart.items,
        total_price=calculate_total(cart),
    )


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получение текущей корзины пользователя."""
    cart = await get_or_create_cart(db, current_user.id)
    return _build_cart_response(cart)


@router.post("/items", response_model=CartResponse)
async def add_single_item(
    data: CartItemAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Добавление одного товара в корзину."""
    try:
        cart = await add_item_to_cart(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _build_cart_response(cart)


@router.post("/items/bulk", response_model=CartResponse)
async def add_multiple_items(
    data: CartItemsAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Массовое добавление товаров в корзину одним запросом."""
    try:
        cart = await add_items_to_cart(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _build_cart_response(cart)


@router.delete("/items", response_model=CartResponse)
async def remove_item(
    data: CartItemRemove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление конкретного товара из корзины."""
    try:
        cart = await remove_item_from_cart(db, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _build_cart_response(cart)


@router.delete("/", response_model=CartResponse)
async def clear(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Полная очистка корзины пользователя."""
    cart = await clear_cart(db, current_user.id)
    return _build_cart_response(cart)
