from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

# 库内 DATETIME 与业务展示均使用北京时间（东八区，naive）
TZ_CN = ZoneInfo("Asia/Shanghai")


def now_cn() -> datetime:
    """当前北京时间（无时区标记，直接写入 MySQL DATETIME）。"""
    return datetime.now(TZ_CN).replace(tzinfo=None)


def as_cn(dt: datetime) -> datetime:
    """规范为北京时间 naive（从库读出或带时区的值）。"""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(TZ_CN).replace(tzinfo=None)


def format_dt(dt: Optional[datetime]) -> Optional[str]:
    """格式化为 yyyy-MM-dd HH:mm（已是北京时间则直接格式化）。"""
    if dt is None:
        return None
    return as_cn(dt).strftime("%Y-%m-%d %H:%M")


# 兼容旧调用名
utcnow = now_cn
utcnow_naive = now_cn
