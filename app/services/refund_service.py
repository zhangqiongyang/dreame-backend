from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import (
    REFUND_REASONS,
    REFUND_STATUS_LABEL,
    OrderStatus,
    RefundStatus,
)
from app.core.exceptions import BusinessError
from app.models.order import Order
from app.models.refund import Refund, RefundStatusLog
from app.models.user import User
from app.schemas.admin import AdminRefundRowOut
from app.schemas.refund import CreateRefundIn, RefundDetailOut, RefundEligibilityOut, RefundStepOut
from app.services.order_service import _load_order, _log_status
from app.utils.datetime_util import format_dt, utcnow
from app.utils.money import cents_to_yuan


async def generate_refund_no(session: AsyncSession) -> str:
    today = utcnow().strftime("%Y%m%d")
    prefix = f"RF{today}"
    result = await session.execute(
        select(func.max(Refund.refund_no)).where(Refund.refund_no.like(f"{prefix}%"))
    )
    last = result.scalar_one_or_none()
    seq = 1
    if last and len(last) > len(prefix):
        try:
            seq = int(last[len(prefix) :]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"


async def check_eligibility(session: AsyncSession, user: User, order_id: int) -> RefundEligibilityOut:
    order = await _load_order(session, order_id, user.id)
    if order.status == OrderStatus.SHIPPED:
        return RefundEligibilityOut(canApply=False, message="已发货，暂不支持在线退款")
    if order.status in (OrderStatus.COMPLETED, OrderStatus.CLOSED, OrderStatus.REFUNDED):
        return RefundEligibilityOut(canApply=False, message="当前订单状态不可申请退款")
    if order.status != OrderStatus.PENDING_SHIPPING:
        return RefundEligibilityOut(canApply=False, message="仅待发货订单可申请退款")
    if order.refund and order.refund.status == RefundStatus.PENDING:
        return RefundEligibilityOut(canApply=False, message="已有进行中的退款申请")
    return RefundEligibilityOut(
        canApply=True,
        message="未发货，可退全款",
        refundAmount=cents_to_yuan(order.pay_amount_cents),
    )


def _build_steps(refund: Refund) -> List[RefundStepOut]:
    logs = sorted(refund.status_logs, key=lambda x: x.created_at)
    submitted = next((l for l in logs if l.status == "submitted"), None)
    steps = [
        RefundStepOut(
            title="已提交申请",
            time=format_dt(submitted.created_at) if submitted else format_dt(refund.created_at),
            remark=None,
            done=True,
            active=False,
        ),
    ]
    if refund.status == RefundStatus.PENDING:
        steps.append(
            RefundStepOut(
                title="商家审核中",
                time=None,
                remark="预计1-3个工作日完成审核",
                done=False,
                active=True,
            )
        )
        steps.append(
            RefundStepOut(title="审核结果", time=None, remark="等待审核中...", done=False, active=False)
        )
    elif refund.status == RefundStatus.APPROVED:
        steps.append(
            RefundStepOut(
                title="商家审核中",
                time=format_dt(refund.audited_at),
                remark=None,
                done=True,
                active=False,
            )
        )
        steps.append(
            RefundStepOut(
                title="审核通过",
                time=format_dt(refund.audited_at),
                remark="退款将在1-7个工作日原路返回（假支付阶段仅更新状态）",
                done=True,
                active=False,
            )
        )
    else:
        steps.append(
            RefundStepOut(
                title="商家审核中",
                time=format_dt(refund.audited_at),
                remark=None,
                done=True,
                active=False,
            )
        )
        steps.append(
            RefundStepOut(
                title="审核驳回",
                time=format_dt(refund.audited_at),
                remark=refund.audit_remark or "审核未通过",
                done=True,
                active=False,
            )
        )
    return steps


def refund_to_detail(refund: Refund) -> RefundDetailOut:
    return RefundDetailOut(
        id=str(refund.id),
        refundNo=refund.refund_no,
        orderId=str(refund.order_id),
        status=refund.status,
        statusLabel=REFUND_STATUS_LABEL.get(refund.status, refund.status),
        amount=cents_to_yuan(refund.amount_cents),
        reason=refund.reason,
        reasonText=refund.reason_text,
        steps=_build_steps(refund),
    )


async def create_refund(
    session: AsyncSession, user: User, order_id: int, body: CreateRefundIn
) -> RefundDetailOut:
    if body.reason not in REFUND_REASONS:
        raise BusinessError("退款原因无效")

    eligible = await check_eligibility(session, user, order_id)
    if not eligible.canApply:
        raise BusinessError(eligible.message)

    order = await _load_order(session, order_id, user.id)
    now = utcnow()
    refund_no = await generate_refund_no(session)

    refund = Refund(
        refund_no=refund_no,
        order_id=order.id,
        user_id=user.id,
        amount_cents=order.pay_amount_cents,
        reason=body.reason,
        reason_text=body.reasonText,
        status=RefundStatus.PENDING,
    )
    session.add(refund)
    await session.flush()
    session.add(
        RefundStatusLog(
            refund_id=refund.id,
            status="submitted",
            remark="用户提交退款申请",
            created_at=now,
        )
    )
    session.add(
        RefundStatusLog(
            refund_id=refund.id,
            status=RefundStatus.PENDING,
            remark="等待商家审核",
            created_at=now,
        )
    )
    await session.commit()

    result = await session.execute(
        select(Refund)
        .where(Refund.id == refund.id)
        .options(selectinload(Refund.status_logs))
    )
    refund = result.scalar_one()
    return refund_to_detail(refund)


async def get_refund(session: AsyncSession, user: User, refund_id: int) -> RefundDetailOut:
    result = await session.execute(
        select(Refund)
        .where(Refund.id == refund_id, Refund.user_id == user.id)
        .options(selectinload(Refund.status_logs))
    )
    refund = result.scalar_one_or_none()
    if refund is None:
        raise BusinessError("退款单不存在")
    return refund_to_detail(refund)


async def approve_refund(session: AsyncSession, refund_id: int, remark: Optional[str]) -> None:
    refund = await _get_refund_admin(session, refund_id)
    if refund.status != RefundStatus.PENDING:
        raise BusinessError("退款单已处理")

    order = await _load_order(session, refund.order_id)
    now = utcnow()
    refund.status = RefundStatus.APPROVED
    refund.audit_remark = remark
    refund.audited_at = now

    prev = order.status
    order.status = OrderStatus.REFUNDED
    session.add(
        RefundStatusLog(refund_id=refund.id, status=RefundStatus.APPROVED, remark=remark, created_at=now)
    )
    await _log_status(session, order, prev, order.status, "admin", None, "退款审核通过")
    await session.commit()


async def reject_refund(session: AsyncSession, refund_id: int, remark: Optional[str]) -> None:
    refund = await _get_refund_admin(session, refund_id)
    if refund.status != RefundStatus.PENDING:
        raise BusinessError("退款单已处理")

    now = utcnow()
    refund.status = RefundStatus.REJECTED
    refund.audit_remark = remark
    refund.audited_at = now
    session.add(
        RefundStatusLog(refund_id=refund.id, status=RefundStatus.REJECTED, remark=remark, created_at=now)
    )
    await session.commit()


async def _get_refund_admin(session: AsyncSession, refund_id: int) -> Refund:
    refund = await session.get(Refund, refund_id)
    if refund is None:
        raise BusinessError("退款单不存在")
    return refund


async def list_refunds_admin(
    session: AsyncSession, *, status: Optional[str] = None
) -> List[AdminRefundRowOut]:
    q = (
        select(Refund, Order, User)
        .join(Order, Refund.order_id == Order.id)
        .join(User, Refund.user_id == User.id)
        .order_by(Refund.created_at.desc())
    )
    if status in ("pending", "待审核"):
        q = q.where(Refund.status == RefundStatus.PENDING)
    elif status in ("approved", "rejected", "已处理", "已拒绝"):
        q = q.where(Refund.status != RefundStatus.PENDING)

    result = await session.execute(q)
    rows = []
    for refund, order, user in result.all():
        name = user.nickname or f"用户{user.id}"
        rows.append(
            AdminRefundRowOut(
                id=str(refund.id),
                refundNo=refund.refund_no,
                orderNo=order.order_no,
                user=name,
                amount=cents_to_yuan(refund.amount_cents),
                reason=refund.reason,
                status=REFUND_STATUS_LABEL.get(refund.status, refund.status),
            )
        )
    return rows
