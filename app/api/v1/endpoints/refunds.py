from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, success
from app.schemas.refund import CreateRefundIn, RefundDetailOut, RefundEligibilityOut
from app.services import refund_service

router = APIRouter(prefix="", tags=["refunds"])


@router.get("/orders/{order_id}/refund-eligibility", response_model=ApiResponse[RefundEligibilityOut])
async def refund_eligibility(
    order_id: int, db: DbSession, user: CurrentUser
) -> ApiResponse[RefundEligibilityOut]:
    return success(await refund_service.check_eligibility(db, user, order_id))


@router.post("/orders/{order_id}/refunds", response_model=ApiResponse[RefundDetailOut])
async def create_refund(
    order_id: int, body: CreateRefundIn, db: DbSession, user: CurrentUser
) -> ApiResponse[RefundDetailOut]:
    return success(await refund_service.create_refund(db, user, order_id, body))


@router.get("/refunds/{refund_id}", response_model=ApiResponse[RefundDetailOut])
async def get_refund(refund_id: int, db: DbSession, user: CurrentUser) -> ApiResponse[RefundDetailOut]:
    return success(await refund_service.get_refund(db, user, refund_id))
