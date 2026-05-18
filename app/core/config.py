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

    database_url: str = ""
    database_url_sync: str = ""

    wechat_appid: str = ""
    wechat_secret: str = ""
    wechat_mock: bool = True

    jwt_secret: str = "change-me-in-production"
    jwt_expire_seconds: int = 604800

    admin_token: str = "dreame-admin-dev"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_display_name: str = "Admin User"

    order_expire_hours: int = 24
    auto_complete_shipped_days: int = 7

    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
