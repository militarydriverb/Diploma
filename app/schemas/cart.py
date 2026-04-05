from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    """Схема добавления одного товара в корзину."""
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemsAdd(BaseModel):
    """Схема массового добавления товаров в корзину."""
    items: list[CartItemAdd] = Field(min_length=1)


class CartItemRemove(BaseModel):
    """Схема удаления товара из корзины."""
    product_id: int


class CartItemResponse(BaseModel):
    """Позиция корзины в ответе."""
    id: int
    product_id: int
    quantity: int
    product: ProductResponse

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Полное представление корзины с итоговой стоимостью."""
    id: int
    user_id: int
    items: list[CartItemResponse]
    # Итоговая стоимость вычисляется на сервере, не хранится в БД
    total_price: int

    model_config = {"from_attributes": True}
