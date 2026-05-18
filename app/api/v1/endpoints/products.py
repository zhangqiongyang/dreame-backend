from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.response import ApiResponse, success
from app.schemas.product import ProductCardOut, ProductDetailOut
from app.services import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ApiResponse[list[ProductCardOut]])
async def list_products(db: DbSession) -> ApiResponse[list[ProductCardOut]]:
    return success(await product_service.list_products(db))


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailOut])
async def get_product(product_id: str, db: DbSession) -> ApiResponse[ProductDetailOut]:
    return success(await product_service.get_product(db, product_id))
