from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # URL основной базы данных — задаётся через .env или переменную окружения
    DATABASE_URL: str
    # Секретный ключ для подписи JWT — обязательно задать в окружении
    SECRET_KEY: str
    # Алгоритм подписи JWT
    ALGORITHM: str = "HS256"
    # Время жизни токена доступа в минутах
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
