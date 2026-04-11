import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator


class UserRegister(BaseModel):
    """Схема регистрации пользователя."""

    full_name: str
    email: EmailStr
    phone: str
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Проверяет требования к паролю: длина, латиница, заглавная буква, спецсимвол."""
        if len(v) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов")
        if not re.match(r"^[a-zA-Z0-9$%&!:]+$", v):
            raise ValueError(
                "Пароль должен содержать только латинские буквы, цифры и спецсимволы ($%&!:)"
            )
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r"[$%&!:]", v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол ($%&!:)")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Проверяет формат телефона: +7 и ровно 10 цифр."""
        if not re.match(r"^\+7\d{10}$", v):
            raise ValueError("Телефон должен начинаться с +7 и содержать 10 цифр")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        """Проверяет совпадение пароля и его подтверждения."""
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        return self


class UserLogin(BaseModel):
    """Схема входа: логин (email или телефон) и пароль."""

    login: str
    password: str


class UserResponse(BaseModel):
    """Ответ с данными пользователя (без пароля)."""

    id: int
    full_name: str
    email: str
    phone: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT-токен доступа."""

    access_token: str
    token_type: str = "bearer"
