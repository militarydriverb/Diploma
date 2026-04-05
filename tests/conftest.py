import asyncio

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.services.auth import hash_password

# URL тестовой базы данных
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:Qwerty123@localhost:5432/diploma_test"
)


def _make_engine():
    """Создаёт движок без пула соединений — безопасно при смене event loop."""
    return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


# ---------------------------------------------------------------------------
# Хуки pytest: создаём/удаляем схему через asyncio.run() вне pytest-asyncio
# ---------------------------------------------------------------------------


def pytest_sessionstart(session):
    """Создаём таблицы один раз перед всеми тестами (drop_all + create_all)."""

    async def _setup():
        engine = _make_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_setup())


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Очищаем таблицы перед каждым тестом (TRUNCATE CASCADE).
    Очистка до yield — следующий тест не зависнет, даже если предыдущий был убит.
    """
    engine = _make_engine()
    async with engine.connect() as conn:
        # Ограничиваем время ожидания блокировки — защита от зависших транзакций
        await conn.execute(text("SET lock_timeout = '5s'"))
        await conn.execute(
            text(
                "TRUNCATE TABLE cart_items, carts, products, users RESTART IDENTITY CASCADE"
            )
        )
        await conn.commit()
    await engine.dispose()
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Сессия базы данных для прямого взаимодействия в тестах."""
    engine = _make_engine()
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTP-клиент с подменённой зависимостью базы данных."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession) -> User:
    """Обычный пользователь для тестов."""
    user = User(
        full_name="Иванов Иван Иванович",
        email="test@example.com",
        phone="+71234567890",
        hashed_password=hash_password("Password!1"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Администратор для тестов."""
    user = User(
        full_name="Петров Пётр Петрович",
        email="admin@example.com",
        phone="+79876543210",
        hashed_password=hash_password("AdminPass!1"),
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(client: AsyncClient, regular_user: User) -> str:
    """JWT-токен обычного пользователя."""
    resp = await client.post(
        "/auth/login", json={"login": "test@example.com", "password": "Password!1"}
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """JWT-токен администратора."""
    resp = await client.post(
        "/auth/login", json={"login": "admin@example.com", "password": "AdminPass!1"}
    )
    return resp.json()["access_token"]
