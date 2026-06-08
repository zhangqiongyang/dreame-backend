from pydantic import BaseModel, Field, field_validator

from app.utils.phone import validate_cn_mobile


class ReceiverIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=11, max_length=20)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_cn_mobile(v)
    province: str = Field(default="", max_length=32)
    city: str = Field(default="", max_length=32)
    district: str = Field(default="", max_length=32)
    detail: str = Field(min_length=1, max_length=255)

    def full_address(self) -> str:
        parts = [self.province, self.city, self.district, self.detail]
        return "".join(p for p in parts if p)
