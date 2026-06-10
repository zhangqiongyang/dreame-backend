from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 固定指向 dreame-backend/.env，避免从仓库根目录启动时读不到配置而误走 Mock
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Dreame API"
    debug: bool = True

    database_url: str = ""
    database_url_sync: str = ""

    wechat_appid: str = ""
    wechat_secret: str = ""
    # 未配置 AppID/Secret 时自动走 Mock；三者齐全且 MOCK=false 时调微信 jscode2session
    wechat_mock: bool = False

    jwt_secret: str = "change-me-in-production"
    jwt_expire_seconds: int = 604800

    admin_token: str = "dreame-admin-dev"
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_display_name: str = "Admin User"

    order_expire_hours: int = 24
    auto_complete_shipped_days: int = 7

    cors_origins: str = "*"

    backend_root: Path = _BACKEND_ROOT
    upload_dir: str = "uploads"
    public_base_url: str = ""

    @field_validator("wechat_mock", mode="before")
    @classmethod
    def _parse_bool(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        return str(v).strip().lower() in ("1", "true", "yes", "on")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
