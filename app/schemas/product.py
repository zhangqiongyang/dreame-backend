from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class ProductCardOut(BaseModel):
    id: str
    name: str
    price: int
    tags: List[str]
    image: str
    hot: Optional[bool] = None


class ProductDetailOut(ProductCardOut):
    marketPrice: Optional[int] = None
    promo: Optional[str] = None
    title: str
    specTags: List[str]
    params: List[dict]
    highlights: List[dict]
    detailImages: List[str]
    heroImage: str


class ProductParamIn(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=128)


class ProductHighlightIn(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    desc: str = Field(min_length=1, max_length=512)


class AdminProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=512)
    price: int = Field(gt=0)
    marketPrice: Optional[int] = Field(default=None, gt=0)
    tags: List[str] = Field(min_length=1)
    specTags: List[str] = Field(default_factory=list)
    coverUrl: HttpUrl
    heroImage: HttpUrl
    detailImages: List[HttpUrl] = Field(min_length=1)
    params: List[ProductParamIn] = Field(min_length=1)
    highlights: List[ProductHighlightIn] = Field(min_length=1)
    isHot: bool = False
    sort: Optional[int] = Field(default=None, ge=0)
    status: Literal["active", "inactive"] = "active"

    @field_validator("tags")
    @classmethod
    def strip_tags(cls, value: List[str]) -> List[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("至少填写一个标签")
        return cleaned

    @field_validator("specTags")
    @classmethod
    def strip_spec_tags(cls, value: List[str]) -> List[str]:
        return [item.strip() for item in value if item and item.strip()]

    @model_validator(mode="after")
    def validate_market_price(self) -> "AdminProductIn":
        if self.marketPrice is not None and self.marketPrice < self.price:
            raise ValueError("市场价不能低于现价")
        return self


class AdminProductRowOut(BaseModel):
    id: str
    name: str
    price: int
    marketPrice: Optional[int] = None
    coverUrl: str
    isHot: bool
    sort: int
    status: str
    statusLabel: str
    createdAt: str
    updatedAt: str


class AdminProductOut(AdminProductIn):
    id: str
    createdAt: str
    updatedAt: str


class ProductStatusPatchIn(BaseModel):
    status: Literal["active", "inactive"]
