from typing import List, Optional

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    market_price_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cover_url: Mapped[str] = mapped_column(String(512), nullable=False)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    promo: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    spec_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    params: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    highlights: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    hero_image: Mapped[str] = mapped_column(String(512), nullable=False)
    detail_images: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
