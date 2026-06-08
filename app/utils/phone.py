"""中国大陆 11 位手机号校验（统一规则）。"""

from __future__ import annotations

import re
from typing import Optional

# 1 开头，第二位 3-9，共 11 位数字
CN_MOBILE_RE = re.compile(r"^1[3-9]\d{9}$")

PHONE_INVALID_MSG = "手机号格式不正确"


def normalize_phone(value: str) -> str:
    return value.strip().replace(" ", "").replace("-", "")


def validate_cn_mobile(value: str) -> str:
    phone = normalize_phone(value)
    if not CN_MOBILE_RE.fullmatch(phone):
        raise ValueError(PHONE_INVALID_MSG)
    return phone


def validate_cn_mobile_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return validate_cn_mobile(value)
