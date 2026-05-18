from __future__ import annotations

from typing import Union


def cents_to_yuan(cents: int) -> int:
    return cents // 100


def yuan_to_cents(yuan: Union[int, float]) -> int:
    return int(round(float(yuan) * 100))


def mask_phone(phone: str) -> str:
    if len(phone) >= 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone
