from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # URL основной базы данных (переопределяется через .env или переменные окружения)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/diploma"
    # Секретный ключ для подписи JWT (обязательно смените в продакшене)
    SECRET_KEY: str = "super-secret-key-change-in-production"
    # Алгоритм подписи JWT
    ALGORITHM: str = "HS256"
    # Время жизни токена доступа в минутах
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
