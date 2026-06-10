from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PRODUCT_STATUS_LABEL, ProductStatus
from app.core.exceptions import BusinessError
from app.models.product import Product
from app.schemas.product import (
    AdminProductIn,
    AdminProductOut,
    AdminProductRowOut,
    ProductCardOut,
    ProductDetailOut,
)
from app.utils.datetime_util import format_dt
from app.utils.ids import IdPrefix, generate_unique_id
from app.utils.money import cents_to_yuan, yuan_to_cents


def product_to_card(p: Product) -> ProductCardOut:
    return ProductCardOut(
        id=p.id,
        name=p.name,
        price=cents_to_yuan(p.price_cents),
        tags=p.tags or [],
        image=p.cover_url,
        hot=p.is_hot or None,
    )


def product_to_detail(p: Product) -> ProductDetailOut:
    card = product_to_card(p)
    return ProductDetailOut(
        **card.model_dump(),
        marketPrice=cents_to_yuan(p.market_price_cents) if p.market_price_cents else None,
        promo=p.promo,
        title=p.title,
        specTags=p.spec_tags or [],
        params=p.params or [],
        highlights=p.highlights or [],
        detailImages=p.detail_images or [],
        heroImage=p.hero_image,
    )


def _status_label(status: str) -> str:
    return PRODUCT_STATUS_LABEL.get(status, status)


def product_to_admin_row(p: Product) -> AdminProductRowOut:
    return AdminProductRowOut(
        id=p.id,
        name=p.name,
        price=cents_to_yuan(p.price_cents),
        marketPrice=cents_to_yuan(p.market_price_cents) if p.market_price_cents else None,
        coverUrl=p.cover_url,
        isHot=bool(p.is_hot),
        sort=p.sort,
        status=p.status,
        statusLabel=_status_label(p.status),
        createdAt=format_dt(p.created_at) or "",
        updatedAt=format_dt(p.updated_at) or "",
    )


def product_to_admin_out(p: Product) -> AdminProductOut:
    return AdminProductOut(
        id=p.id,
        name=p.name,
        title=p.title,
        price=cents_to_yuan(p.price_cents),
        marketPrice=cents_to_yuan(p.market_price_cents) if p.market_price_cents else None,
        promo=p.promo,
        tags=p.tags or [],
        specTags=p.spec_tags or [],
        coverUrl=p.cover_url,
        heroImage=p.hero_image,
        detailImages=p.detail_images or [],
        params=p.params or [],
        highlights=p.highlights or [],
        isHot=bool(p.is_hot),
        sort=p.sort,
        status=p.status,
        createdAt=format_dt(p.created_at) or "",
        updatedAt=format_dt(p.updated_at) or "",
    )


def _apply_product_in(product: Product, body: AdminProductIn) -> None:
    product.name = body.name
    product.title = body.title
    product.price_cents = yuan_to_cents(body.price)
    product.market_price_cents = yuan_to_cents(body.marketPrice) if body.marketPrice else None
    product.promo = None
    product.tags = body.tags
    product.spec_tags = body.specTags
    product.cover_url = str(body.coverUrl)
    product.hero_image = str(body.heroImage)
    product.detail_images = [str(url) for url in body.detailImages]
    product.params = [item.model_dump() for item in body.params]
    product.highlights = [item.model_dump() for item in body.highlights]
    product.is_hot = body.isHot
    if body.sort is not None:
        product.sort = body.sort
    product.status = body.status


async def list_products(session: AsyncSession) -> list[ProductCardOut]:
    result = await session.execute(
        select(Product).where(Product.status == ProductStatus.ACTIVE).order_by(Product.sort.asc())
    )
    return [product_to_card(p) for p in result.scalars().all()]


async def get_product(session: AsyncSession, product_id: str) -> ProductDetailOut:
    product = await session.get(Product, product_id)
    if product is None or product.status != ProductStatus.ACTIVE:
        raise BusinessError("商品不存在或已下架")
    return product_to_detail(product)


async def _get_product_or_raise(session: AsyncSession, product_id: str) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise BusinessError("商品不存在")
    return product


async def _next_sort(session: AsyncSession) -> int:
    max_sort = await session.scalar(select(func.coalesce(func.max(Product.sort), 0)))
    return int(max_sort or 0) + 1


async def list_admin_products(
    session: AsyncSession,
    *,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> list[AdminProductRowOut]:
    q = select(Product).order_by(Product.sort.asc(), Product.created_at.desc())
    if status:
        q = q.where(Product.status == status)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(
            or_(Product.id.like(kw), Product.name.like(kw), Product.title.like(kw))
        )

    offset = max(page - 1, 0) * page_size
    result = await session.execute(q.offset(offset).limit(min(page_size, 100)))
    return [product_to_admin_row(p) for p in result.scalars().all()]


async def get_admin_product(session: AsyncSession, product_id: str) -> AdminProductOut:
    product = await _get_product_or_raise(session, product_id)
    return product_to_admin_out(product)


async def _generate_product_id(session: AsyncSession) -> str:
    async def exists(product_id: str) -> bool:
        return await session.get(Product, product_id) is not None

    return await generate_unique_id(session, IdPrefix.PRODUCT, exists_query=exists)


async def create_product(session: AsyncSession, body: AdminProductIn) -> AdminProductOut:
    product_id = await _generate_product_id(session)
    sort = body.sort if body.sort is not None else await _next_sort(session)
    product = Product(
        id=product_id,
        name=body.name,
        title=body.title,
        price_cents=yuan_to_cents(body.price),
        market_price_cents=yuan_to_cents(body.marketPrice) if body.marketPrice else None,
        promo=None,
        tags=body.tags,
        spec_tags=body.specTags or [],
        cover_url=str(body.coverUrl),
        hero_image=str(body.heroImage),
        detail_images=[str(url) for url in body.detailImages],
        params=[item.model_dump() for item in body.params],
        highlights=[item.model_dump() for item in body.highlights],
        is_hot=body.isHot,
        sort=sort,
        status=body.status,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product_to_admin_out(product)


async def update_product(
    session: AsyncSession, product_id: str, body: AdminProductIn
) -> AdminProductOut:
    product = await _get_product_or_raise(session, product_id)
    _apply_product_in(product, body)
    await session.commit()
    await session.refresh(product)
    return product_to_admin_out(product)


async def patch_product_status(
    session: AsyncSession, product_id: str, status: str
) -> AdminProductOut:
    if status not in (ProductStatus.ACTIVE, ProductStatus.INACTIVE):
        raise BusinessError("商品状态无效")
    product = await _get_product_or_raise(session, product_id)
    product.status = status
    await session.commit()
    await session.refresh(product)
    return product_to_admin_out(product)
