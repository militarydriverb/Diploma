from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_active_products(db: AsyncSession) -> list[Product]:
    """Возвращает все активные товары."""
    result = await db.execute(select(Product).where(Product.is_active == True))
    return list(result.scalars().all())


async def get_product_by_id(db: AsyncSession, product_id: int) -> Product | None:
    """Возвращает товар по ID или None."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    """Создаёт новый товар и сохраняет его в БД."""
    product = Product(
        name=data.name,
        price=data.price,
        is_active=data.is_active,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(db: AsyncSession, product_id: int, data: ProductUpdate) -> Product | None:
    """
    Обновляет только переданные поля товара.
    Возвращает None, если товар не найден.
    """
    product = await get_product_by_id(db, product_id)
    if not product:
        return None
    # Обновляем только явно переданные поля (exclude_unset)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """Удаляет товар по ID. Возвращает False, если товар не найден."""
    product = await get_product_by_id(db, product_id)
    if not product:
        return False
    await db.delete(product)
    await db.commit()
    return True
