from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ORDER_STATUS_LABEL, OrderStatus, UserStatus
from app.core.exceptions import BusinessError
from app.models.order import Order
from app.models.user import User
from app.schemas.admin import AdminOrderRowOut, AdminUserRowOut, DashboardOut
from app.services.order_service import _load_order, _resolve_status_filter, order_to_detail
from app.utils.datetime_util import format_dt, now_cn
from app.utils.money import cents_to_yuan, mask_phone


def _phone_authorized_filter():
    """仅展示已完成手机号授权的用户（与小程序「已登录」定义一致）。"""
    return User.phone.is_not(None)


def _shanghai_today_range() -> tuple[datetime, datetime]:
    now = now_cn()
    start = datetime.combine(now.date(), time.min)
    end = start + timedelta(days=1)
    return start, end


async def get_dashboard(session: AsyncSession) -> DashboardOut:
    start, end = _shanghai_today_range()

    today_orders = await session.scalar(
        select(func.count(Order.id)).where(Order.created_at >= start, Order.created_at < end)
    )
    today_sales_cents = await session.scalar(
        select(func.coalesce(func.sum(Order.pay_amount_cents), 0)).where(
            Order.paid_at.is_not(None),
            Order.paid_at >= start,
            Order.paid_at < end,
            Order.status.not_in([OrderStatus.CLOSED]),
        )
    )
    pending_ship = await session.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING_SHIPPING)
    )
    new_users = await session.scalar(
        select(func.count(User.id)).where(
            User.created_at >= start,
            User.created_at < end,
            _phone_authorized_filter(),
        )
    )

    return DashboardOut(
        todayOrders=today_orders or 0,
        todaySales=cents_to_yuan(int(today_sales_cents or 0)),
        pendingShipCount=pending_ship or 0,
        newUsers=new_users or 0,
    )


async def list_admin_orders(
    session: AsyncSession,
    *,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> List[AdminOrderRowOut]:
    q = (
        select(Order, User)
        .join(User, Order.user_id == User.user_no)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(
            (Order.order_no.like(kw))
            | (User.user_no.like(kw))
            | (User.nickname.like(kw))
            | (User.phone.like(kw))
            | (Order.receiver_phone.like(kw))
            | (Order.receiver_name.like(kw))
        )
    if status and status not in ("全部", "all", ""):
        code = _resolve_status_filter(status.strip())
        if code:
            q = q.where(Order.status == code)

    offset = max(page - 1, 0) * page_size
    result = await session.execute(q.offset(offset).limit(min(page_size, 100)))
    rows = []
    for order, user in result.all():
        name = user.nickname or order.receiver_name or f"用户{user.user_no}"
        first_item = order.items[0] if order.items else None
        product_title = first_item.title if first_item else "—"
        qty = first_item.qty if first_item else 1
        phone_raw = user.phone or order.receiver_phone
        rows.append(
            AdminOrderRowOut(
                id=order.order_no,
                orderNo=order.order_no,
                user=name,
                userPhone=mask_phone(phone_raw) if phone_raw else "—",
                productTitle=product_title,
                qty=qty,
                amount=cents_to_yuan(order.pay_amount_cents),
                status=ORDER_STATUS_LABEL.get(order.status, order.status),
                statusCode=order.status,
                createdAt=format_dt(order.created_at) or "",
            )
        )
    return rows


async def get_admin_order_detail(session: AsyncSession, order_no: str) -> Dict[str, Any]:
    order = await _load_order(session, order_no)
    detail = order_to_detail(order, mask_receiver_phone=False)
    logs = sorted(order.status_logs, key=lambda x: x.created_at)
    return {
        "order": detail.model_dump(),
        "statusLogs": [
            {
                "fromStatus": log.from_status,
                "toStatus": log.to_status,
                "operatorType": log.operator_type,
                "remark": log.remark,
                "createdAt": format_dt(log.created_at),
            }
            for log in logs
        ],
    }


async def list_users(
    session: AsyncSession, *, keyword: Optional[str] = None, page: int = 1, page_size: int = 20
) -> List[AdminUserRowOut]:
    q = select(User).where(_phone_authorized_filter()).order_by(User.created_at.desc())
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.where(
            (User.user_no.like(kw))
            | (User.nickname.like(kw))
            | (User.phone.like(kw))
            | (User.openid.like(kw))
        )

    offset = max(page - 1, 0) * page_size
    users = (await session.execute(q.offset(offset).limit(min(page_size, 100)))).scalars().all()

    rows: List[AdminUserRowOut] = []
    for user in users:
        order_count = await session.scalar(
            select(func.count(Order.id)).where(
                Order.user_id == user.user_no,
                Order.status.not_in([OrderStatus.CLOSED, OrderStatus.PENDING_PAYMENT]),
            )
        )
        spent_cents = await session.scalar(
            select(func.coalesce(func.sum(Order.pay_amount_cents), 0)).where(
                Order.user_id == user.user_no,
                Order.paid_at.is_not(None),
                Order.status.not_in([OrderStatus.CLOSED, OrderStatus.REFUNDED]),
            )
        )
        name = user.nickname or f"用户{user.user_no}"
        phone = mask_phone(user.phone) if user.phone else "—"
        status_label = "活跃" if user.status == UserStatus.ACTIVE else "已禁用"
        rows.append(
            AdminUserRowOut(
                id=user.user_no,
                name=name,
                phone=phone,
                orders=order_count or 0,
                spent=cents_to_yuan(int(spent_cents or 0)),
                registeredAt=(format_dt(user.created_at) or "")[:10],
                status=user.status,
                statusLabel=status_label,
            )
        )
    return rows


async def set_user_status(session: AsyncSession, user_no: str, status: str) -> None:
    if status not in (UserStatus.ACTIVE, UserStatus.DISABLED):
        raise BusinessError("用户状态无效")
    result = await session.execute(select(User).where(User.user_no == user_no))
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError("用户不存在")
    user.status = status
    await session.commit()
