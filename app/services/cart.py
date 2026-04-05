from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemAdd, CartItemsAdd, CartItemRemove


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    """Возвращает корзину пользователя, создавая её при первом обращении."""
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
        # После создания загружаем корзину с отношениями
        cart = await _load_cart_with_items(db, cart.id)
    return cart


async def _load_cart_with_items(db: AsyncSession, cart_id: int) -> Cart:
    """Загружает корзину вместе с позициями и товарами (eager loading).
    populate_existing=True гарантирует актуальные данные даже при переиспользовании сессии.
    """
    result = await db.execute(
        select(Cart)
        .where(Cart.id == cart_id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


async def add_items_to_cart(db: AsyncSession, user_id: int, data: CartItemsAdd) -> Cart:
    """
    Добавляет список товаров в корзину.
    Если товар уже есть — увеличивает количество.
    Бросает ValueError, если товар не найден или неактивен.
    """
    cart = await get_or_create_cart(db, user_id)

    for item_data in data.items:
        # Проверяем, что товар существует и активен
        product_result = await db.execute(
            select(Product).where(
                Product.id == item_data.product_id, Product.is_active.is_(True)
            )
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise ValueError(
                f"Товар с id {item_data.product_id} не найден или неактивен"
            )

        # Проверяем, есть ли уже такой товар в корзине
        existing_result = await db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == item_data.product_id,
            )
        )
        existing_item = existing_result.scalar_one_or_none()

        if existing_item:
            # Увеличиваем количество
            existing_item.quantity += item_data.quantity
        else:
            # Создаём новую позицию
            new_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
            )
            db.add(new_item)

    await db.commit()
    return await _load_cart_with_items(db, cart.id)


async def add_item_to_cart(db: AsyncSession, user_id: int, data: CartItemAdd) -> Cart:
    """Добавляет один товар в корзину (обёртка над add_items_to_cart)."""
    return await add_items_to_cart(db, user_id, CartItemsAdd(items=[data]))


async def remove_item_from_cart(
    db: AsyncSession, user_id: int, data: CartItemRemove
) -> Cart:
    """
    Удаляет позицию из корзины.
    Бросает ValueError, если товара нет в корзине.
    """
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == data.product_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ValueError(f"Товар с id {data.product_id} не найден в корзине")

    await db.delete(item)
    await db.commit()
    return await _load_cart_with_items(db, cart.id)


async def clear_cart(db: AsyncSession, user_id: int) -> Cart:
    """Удаляет все позиции из корзины пользователя."""
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    items = result.scalars().all()
    for item in items:
        await db.delete(item)

    await db.commit()
    return await _load_cart_with_items(db, cart.id)


def calculate_total(cart: Cart) -> int:
    """Вычисляет итоговую стоимость корзины: сумма (цена × количество) по всем позициям."""
    return sum(item.product.price * item.quantity for item in cart.items)
