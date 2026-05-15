from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Dreame API"
    debug: bool = True

    # 应用异步连接：mysql+aiomysql://...
    database_url: str = ""

    # Alembic 同步连接：mysql+pymysql://...
    database_url_sync: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
