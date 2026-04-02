from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import (
    create_product,
    delete_product,
    get_active_products,
    get_product_by_id,
    update_product,
)

router = APIRouter(prefix="/products", tags=["Товары"])


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Список всех активных товаров. Доступно авторизованным пользователям."""
    return await get_active_products(db)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Создание нового товара. Только для администратора."""
    return await create_product(db, data)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Получение товара по ID. Доступно авторизованным пользователям."""
    product = await get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Частичное обновление товара. Только для администратора."""
    product = await update_product(db, product_id, data)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Удаление товара. Только для администратора."""
    success = await delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
