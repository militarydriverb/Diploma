from datetime import datetime

from pydantic import BaseModel, field_validator


class ProductCreate(BaseModel):
    """Схема создания нового товара."""
    name: str
    price: int
    is_active: bool = True

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: int) -> int:
        """Цена не может быть отрицательной."""
        if v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Название не может быть пустым."""
        if not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()


class ProductUpdate(BaseModel):
    """Схема частичного обновления товара (все поля опциональны)."""
    name: str | None = None
    price: int | None = None
    is_active: bool | None = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Цена не может быть отрицательной")
        return v


class ProductResponse(BaseModel):
    """Ответ с данными товара."""
    id: int
    name: str
    price: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}
