from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.user import UserRegister


def hash_password(password: str) -> str:
    """Возвращает bcrypt-хеш пароля."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает открытый пароль с хешем."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    """Создаёт подписанный JWT-токен с временем истечения."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Декодирует и проверяет JWT-токен. Вызывает исключение при невалидном токене."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """
    Регистрирует нового пользователя.
    Проверяет уникальность email и телефона перед созданием.
    """
    result = await db.execute(
        select(User).where(or_(User.email == data.email, User.phone == data.phone))
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.email == data.email:
            raise ValueError("Пользователь с таким email уже существует")
        raise ValueError("Пользователь с таким телефоном уже существует")

    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, login: str, password: str) -> User | None:
    """
    Аутентифицирует пользователя по email или телефону и паролю.
    Возвращает None, если пользователь не найден или пароль неверен.
    """
    result = await db.execute(
        select(User).where(or_(User.email == login, User.phone == login))
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Возвращает пользователя по ID или None."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
