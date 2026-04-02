from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URL основной базы данных (переопределяется через .env или переменные окружения)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/diploma"
    # URL тестовой базы данных
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/diploma_test"
    # Секретный ключ для подписи JWT (обязательно смените в продакшене)
    SECRET_KEY: str = "super-secret-key-change-in-production"
    # Алгоритм подписи JWT
    ALGORITHM: str = "HS256"
    # Время жизни токена доступа в минутах
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
