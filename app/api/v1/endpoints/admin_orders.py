from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, verify_admin
from app.core.response import ApiResponse, success
from app.schemas.admin import AdminOrderRowOut, ShipOrderIn
from app.schemas.order import OrderDetailOut
from app.services import admin_service, order_service

router = APIRouter(prefix="/admin", tags=["admin-orders"], dependencies=[Depends(verify_admin)])


@router.get("/orders", response_model=ApiResponse[list[AdminOrderRowOut]])
async def list_orders(
    db: DbSession,
    keyword: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[list[AdminOrderRowOut]]:
    return success(
        await admin_service.list_admin_orders(
            db, keyword=keyword, status=status, page=page, page_size=pageSize
        )
    )


@router.get("/orders/{order_id}")
async def get_order(order_id: str, db: DbSession) -> ApiResponse:
    return success(await admin_service.get_admin_order_detail(db, order_id))


@router.post("/orders/{order_id}/ship", response_model=ApiResponse[OrderDetailOut])
async def ship_order(
    order_id: str, body: ShipOrderIn, db: DbSession
) -> ApiResponse[OrderDetailOut]:
    data = await order_service.ship_order(db, order_id, body.carrier, body.trackingNo)
    return success(data)
