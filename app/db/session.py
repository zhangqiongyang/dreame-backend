from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine = None
_session_factory = None


def _ensure_engine() -> None:
    global _engine, _session_factory
    if not settings.database_url:
        return
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            echo=settings.debug,
            connect_args={"init_command": "SET time_zone='+08:00'"},
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    _ensure_engine()
    if _session_factory is None:
        raise RuntimeError("DATABASE_URL 未配置，无法使用数据库。参见 .env.example 与 docs/数据库安装与配置.md")
    async with _session_factory() as session:
        yield session
