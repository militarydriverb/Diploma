from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cart(Base):
    """Корзина пользователя (один-к-одному с User)."""
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # Каждый пользователь имеет ровно одну корзину
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="cart")
    # cascade="all, delete-orphan" — позиции удаляются вместе с корзиной
    items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    """Позиция корзины: товар + количество."""
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")
