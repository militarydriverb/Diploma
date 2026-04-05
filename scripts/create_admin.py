"""
Скрипт создания администратора.

Использование:
    python scripts/create_admin.py --email admin@example.com --password AdminPass!1 --name "Иванов Иван" --phone "+79001234567"

Если пользователь с таким email уже существует — просто выдаёт ему права администратора.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь, чтобы импортировать app.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.user import User
from app.services.auth import hash_password


async def create_admin(email: str, password: str, full_name: str, phone: str) -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with sm() as session:
        # Проверяем, существует ли пользователь
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            # Выдаём права администратора существующему пользователю
            user.is_admin = True
            await session.commit()
            print(f"Пользователь {email} теперь администратор.")
        else:
            # Создаём нового пользователя с правами администратора
            user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                hashed_password=hash_password(password),
                is_admin=True,
            )
            session.add(user)
            await session.commit()
            print(f"Администратор {email} создан.")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Создание администратора")
    parser.add_argument("--email",    required=True, help="Email администратора")
    parser.add_argument("--password", required=True, help="Пароль (мин. 8 симв., заглавная + спецсимвол)")
    parser.add_argument("--name",     required=True, help="Полное имя")
    parser.add_argument("--phone",    required=True, help="Телефон в формате +7XXXXXXXXXX")
    args = parser.parse_args()

    asyncio.run(create_admin(args.email, args.password, args.name, args.phone))


if __name__ == "__main__":
    main()
