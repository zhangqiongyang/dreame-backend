from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, verify_admin
from app.core.response import ApiResponse, success
from app.schemas.product import AdminProductIn, AdminProductOut, AdminProductRowOut, ProductStatusPatchIn
from app.services import product_service

router = APIRouter(prefix="/admin", tags=["admin-products"], dependencies=[Depends(verify_admin)])


@router.get("/products", response_model=ApiResponse[list[AdminProductRowOut]])
async def list_products(
    db: DbSession,
    keyword: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[list[AdminProductRowOut]]:
    return success(
        await product_service.list_admin_products(
            db, keyword=keyword, status=status, page=page, page_size=pageSize
        )
    )


@router.get("/products/{product_id}", response_model=ApiResponse[AdminProductOut])
async def get_product(product_id: str, db: DbSession) -> ApiResponse[AdminProductOut]:
    return success(await product_service.get_admin_product(db, product_id))


@router.post("/products", response_model=ApiResponse[AdminProductOut])
async def create_product(body: AdminProductIn, db: DbSession) -> ApiResponse[AdminProductOut]:
    return success(await product_service.create_product(db, body))


@router.put("/products/{product_id}", response_model=ApiResponse[AdminProductOut])
async def update_product(
    product_id: str, body: AdminProductIn, db: DbSession
) -> ApiResponse[AdminProductOut]:
    return success(await product_service.update_product(db, product_id, body))


@router.patch("/products/{product_id}/status", response_model=ApiResponse[AdminProductOut])
async def patch_product_status(
    product_id: str, body: ProductStatusPatchIn, db: DbSession
) -> ApiResponse[AdminProductOut]:
    return success(await product_service.patch_product_status(db, product_id, body.status))
