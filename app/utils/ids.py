"""业务编号规则（对外暴露的 id 均使用此类编号，不用数据库自增主键）。

| 实体 | 前缀 | 格式 | 示例 |
|------|------|------|------|
| 用户 | U  | U + yyyyMMdd + 8位随机数字 | U2026051812345678 |
| 订单 | DR | DR + yyyyMMdd + 8位随机数字 | DR2026051812345678 |
| 退款 | RF | RF + yyyyMMdd + 8位随机数字 | RF2026051812345678 |
| 商品 | P  | P + yyyyMMdd + 8位随机数字 | P2026051812345678 |

随机段使用 secrets，碰撞时由调用方重试。
"""

from __future__ import annotations

import re
import secrets
from datetime import datetime
from enum import Enum
from typing import Awaitable, Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class IdPrefix(str, Enum):
    USER = "U"
    ORDER = "DR"
    REFUND = "RF"
    PRODUCT = "P"


_PREFIX_PATTERN = {
    IdPrefix.USER: re.compile(r"^U\d{16}$"),
    IdPrefix.ORDER: re.compile(r"^DR\d{16}$"),
    IdPrefix.REFUND: re.compile(r"^RF\d{16}$"),
    IdPrefix.PRODUCT: re.compile(r"^P\d{16}$"),
}


def generate_business_id(prefix: IdPrefix, *, at: Optional[datetime] = None) -> str:
    from app.utils.datetime_util import now_cn

    day = (at or now_cn()).strftime("%Y%m%d")
    suffix = "".join(secrets.choice("0123456789") for _ in range(8))
    return f"{prefix.value}{day}{suffix}"


def is_valid_business_id(value: str, prefix: IdPrefix) -> bool:
    return bool(_PREFIX_PATTERN[prefix].match(value))


async def generate_unique_id(
    session: AsyncSession,
    prefix: IdPrefix,
    *,
    exists_query: Callable[[str], Awaitable[bool]],
    max_attempts: int = 12,
) -> str:
    """exists_query: 传入候选编号，返回 True 表示已占用。"""
    for _ in range(max_attempts):
        candidate = generate_business_id(prefix)
        if not await exists_query(candidate):
            return candidate
    raise RuntimeError(f"无法生成唯一编号: {prefix.value}")
