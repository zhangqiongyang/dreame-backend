from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, verify_admin
from app.core.response import ApiResponse, success
from app.schemas.admin import RefundAuditIn
from app.services import refund_service

router = APIRouter(prefix="/admin", tags=["admin-refunds"], dependencies=[Depends(verify_admin)])


@router.get("/refunds", response_model=ApiResponse)
async def list_refunds(
    db: DbSession, status: Optional[str] = Query(default=None)
) -> ApiResponse:
    return success(await refund_service.list_refunds_admin(db, status=status))


@router.post("/refunds/{refund_id}/approve", response_model=ApiResponse)
async def approve_refund(
    refund_id: str, body: RefundAuditIn, db: DbSession
) -> ApiResponse:
    await refund_service.approve_refund(db, refund_id, body.auditRemark)
    return success()


@router.post("/refunds/{refund_id}/reject", response_model=ApiResponse)
async def reject_refund(refund_id: str, body: RefundAuditIn, db: DbSession) -> ApiResponse:
    await refund_service.reject_refund(db, refund_id, body.auditRemark)
    return success()
