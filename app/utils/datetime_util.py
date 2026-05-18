from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """当前 UTC 时间（timezone-aware）。"""
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    """将 datetime 规范为 UTC aware（MySQL 读出的 naive 按 UTC 解释）。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utcnow_naive() -> datetime:
    """与 MySQL DATETIME 往返一致的 naive UTC，用于 SQL 条件比较。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    local = as_utc(dt).astimezone()
    return local.strftime("%Y-%m-%d %H:%M")
