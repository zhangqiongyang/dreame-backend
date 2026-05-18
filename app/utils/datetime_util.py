from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    local = dt.astimezone() if dt.tzinfo else dt
    return local.strftime("%Y-%m-%d %H:%M")
