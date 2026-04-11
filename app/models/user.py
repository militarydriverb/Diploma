from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # ФИО пользователя
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Email уникален — используется для входа
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    # Телефон уникален — также используется для входа
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    # Пароль хранится в виде bcrypt-хеша
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Признак администратора: управляет правами на CRUD товаров
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связь один-к-одному с корзиной
    cart: Mapped["Cart"] = relationship("Cart", back_populates="user", uselist=False)  # noqa: F821
