from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, success
from app.schemas.order import CreateOrderIn, OrderDetailOut, OrderListItemOut, PayMockOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=ApiResponse[OrderDetailOut])
async def create_order(
    body: CreateOrderIn, db: DbSession, user: CurrentUser
) -> ApiResponse[OrderDetailOut]:
    return success(await order_service.create_order(db, user, body))


@router.get("", response_model=ApiResponse[list[OrderListItemOut]])
async def list_orders(
    db: DbSession,
    user: CurrentUser,
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[list[OrderListItemOut]]:
    return success(
        await order_service.list_orders(db, user, status=status, page=page, page_size=pageSize)
    )


@router.get("/{order_id}", response_model=ApiResponse[OrderDetailOut])
async def get_order(order_id: int, db: DbSession, user: CurrentUser) -> ApiResponse[OrderDetailOut]:
    return success(await order_service.get_order_detail(db, user, order_id))


@router.post("/{order_id}/pay-mock", response_model=ApiResponse[PayMockOut])
async def pay_mock(order_id: int, db: DbSession, user: CurrentUser) -> ApiResponse[PayMockOut]:
    return success(await order_service.pay_mock(db, user, order_id))


@router.post("/{order_id}/cancel", response_model=ApiResponse)
async def cancel_order(order_id: int, db: DbSession, user: CurrentUser) -> ApiResponse:
    await order_service.cancel_order(db, user, order_id)
    return success()
