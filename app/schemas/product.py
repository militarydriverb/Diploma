from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    """Схема создания нового товара."""
    name: str
    price: int = Field(ge=0)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Название не может быть пустым или состоять только из пробелов."""
        v = v.strip()
        if not v:
            raise ValueError("Название не может быть пустым")
        return v


class ProductUpdate(BaseModel):
    """Схема частичного обновления товара (все поля опциональны)."""
    name: str | None = None
    price: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Ответ с данными товара."""
    id: int
    name: str
    price: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}
