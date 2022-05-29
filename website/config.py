from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Получение ссылки на подключение к базе данных"""

    db_url: str = Field(..., env="DATABASE_URL")


settings = Settings()
