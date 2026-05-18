from typing import List, Optional

from pydantic import BaseModel


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
