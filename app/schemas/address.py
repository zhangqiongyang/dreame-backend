from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.utils.phone import validate_cn_mobile, validate_cn_mobile_optional


class AddressBodyIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=11, max_length=20)
    province: str = Field(default="", max_length=32)
    city: str = Field(default="", max_length=32)
    district: str = Field(default="", max_length=32)
    detail: str = Field(min_length=1, max_length=255)
    isDefault: bool = False

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_cn_mobile(v)


class AddressCreateIn(AddressBodyIn):
    pass


class AddressUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    phone: Optional[str] = Field(default=None, max_length=20)
    province: Optional[str] = Field(default=None, max_length=32)
    city: Optional[str] = Field(default=None, max_length=32)
    district: Optional[str] = Field(default=None, max_length=32)
    detail: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isDefault: Optional[bool] = None

    @field_validator("phone", mode="before")
    @classmethod
    def empty_phone_to_none(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        return validate_cn_mobile_optional(v)


class AddressOut(BaseModel):
    id: str
    name: str
    phone: str
    province: str
    city: str
    district: str
    detail: str
    isDefault: bool
    fullAddress: str
