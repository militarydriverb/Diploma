from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Асинхронный движок SQLAlchemy
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Фабрика асинхронных сессий
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""

    pass


async def get_db() -> AsyncSession:
    """Зависимость FastAPI: предоставляет сессию БД на время запроса."""
    async with async_session_maker() as session:
        yield session
