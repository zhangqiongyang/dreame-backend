from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessError
from app.models.product import Product
from app.schemas.product import ProductCardOut, ProductDetailOut
from app.utils.money import cents_to_yuan


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


async def list_products(session: AsyncSession) -> list[ProductCardOut]:
    result = await session.execute(
        select(Product).where(Product.status == "active").order_by(Product.sort.asc())
    )
    return [product_to_card(p) for p in result.scalars().all()]


async def get_product(session: AsyncSession, product_id: str) -> ProductDetailOut:
    product = await session.get(Product, product_id)
    if product is None or product.status != "active":
        raise BusinessError("商品不存在或已下架")
    return product_to_detail(product)
