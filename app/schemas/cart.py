from pydantic import BaseModel, field_validator

from app.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    """Схема добавления одного товара в корзину."""
    product_id: int
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Количество должно быть не менее 1."""
        if v < 1:
            raise ValueError("Количество должно быть не менее 1")
        return v


class CartItemsAdd(BaseModel):
    """Схема массового добавления товаров в корзину."""
    items: list[CartItemAdd]

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list) -> list:
        """Список товаров не может быть пустым."""
        if not v:
            raise ValueError("Список товаров не может быть пустым")
        return v


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
