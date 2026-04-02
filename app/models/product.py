from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    """Модель товара."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Цена в целых единицах (например, копейки или рубли)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Обновляется автоматически при изменении записи
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Только активные товары отображаются пользователям
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="product")
