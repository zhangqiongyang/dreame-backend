from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.constants import ORDER_STATUS_LABEL, OrderStatus
from app.core.exceptions import BusinessError
from app.models.order import Order, OrderItem, OrderStatusLog, Shipment
from app.models.product import Product
from app.models.user import User
from app.models.refund import Refund
from app.schemas.order import (
    CreateOrderIn,
    OrderDetailOut,
    OrderListItemOut,
    PayMockOut,
    ShipmentOut,
)
from app.schemas.refund import OrderRefundOut
from app.services import address_service
from app.core.constants import REFUND_STATUS_LABEL
from app.utils.datetime_util import format_dt, now_cn
from app.utils.ids import IdPrefix, generate_unique_id
from app.utils.money import cents_to_yuan, mask_phone


async def generate_order_no(session: AsyncSession) -> str:
    async def exists(no: str) -> bool:
        r = await session.execute(select(Order.id).where(Order.order_no == no).limit(1))
        return r.scalar_one_or_none() is not None

    return await generate_unique_id(session, IdPrefix.ORDER, exists_query=exists)


async def _log_status(
    session: AsyncSession,
    order: Order,
    from_status: Optional[str],
    to_status: str,
    operator_type: str,
    operator_id: Optional[str] = None,
    remark: Optional[str] = None,
) -> None:
    session.add(
        OrderStatusLog(
            order_id=order.id,
            from_status=from_status,
            to_status=to_status,
            operator_type=operator_type,
            operator_id=operator_id,
            remark=remark,
            created_at=now_cn(),
        )
    )


def _first_item(order: Order) -> OrderItem:
    if not order.items:
        raise BusinessError("订单商品数据异常")
    return order.items[0]


def order_to_list_item(order: Order) -> OrderListItemOut:
    item = _first_item(order)
    return OrderListItemOut(
        id=order.order_no,
        orderNo=order.order_no,
        status=ORDER_STATUS_LABEL.get(order.status, order.status),
        title=item.title,
        qty=item.qty,
        amount=cents_to_yuan(order.pay_amount_cents),
        thumb=item.thumb,
    )


def order_to_detail(order: Order, *, mask_receiver_phone: bool = True) -> OrderDetailOut:
    item = _first_item(order)
    phone = mask_phone(order.receiver_phone) if mask_receiver_phone else order.receiver_phone
    shipment = None
    if order.shipment:
        shipment = ShipmentOut(carrier=order.shipment.carrier, trackingNo=order.shipment.tracking_no)
    refund_reason = None
    refund_out = None
    if order.refund:
        from app.services.refund_service import _build_steps

        r = order.refund
        refund_reason = r.reason
        refund_out = OrderRefundOut(
            refundNo=r.refund_no,
            status=r.status,
            statusLabel=REFUND_STATUS_LABEL.get(r.status, r.status),
            amount=cents_to_yuan(r.amount_cents),
            reason=r.reason,
            reasonText=r.reason_text,
            steps=_build_steps(r),
        )
    return OrderDetailOut(
        id=order.order_no,
        orderNo=order.order_no,
        status=order.status,
        statusLabel=ORDER_STATUS_LABEL.get(order.status, order.status),
        title=item.title,
        qty=item.qty,
        amount=cents_to_yuan(order.pay_amount_cents),
        thumb=item.thumb,
        remark=order.remark,
        paymentMethod=order.payment_method,
        createdAt=format_dt(order.created_at) or "",
        paidAt=format_dt(order.paid_at),
        completedAt=format_dt(order.completed_at),
        receiverName=order.receiver_name,
        receiverPhone=phone,
        receiverAddress=order.receiver_address,
        productAmount=cents_to_yuan(order.product_amount_cents),
        freightAmount=cents_to_yuan(order.freight_amount_cents),
        payAmount=cents_to_yuan(order.pay_amount_cents),
        shipment=shipment,
        refundReason=refund_reason,
        refund=refund_out,
    )


async def _load_order(
    session: AsyncSession, order_no: str, user_id: Optional[int] = None
) -> Order:
    q = (
        select(Order)
        .where(Order.order_no == order_no)
        .options(
            selectinload(Order.items),
            selectinload(Order.shipment),
            selectinload(Order.refund).selectinload(Refund.status_logs),
            selectinload(Order.status_logs),
        )
    )
    if user_id is not None:
        q = q.where(Order.user_id == user_id)
    result = await session.execute(q)
    order = result.scalar_one_or_none()
    if order is None:
        raise BusinessError("订单不存在")
    return order


async def create_order(session: AsyncSession, user: User, body: CreateOrderIn) -> OrderDetailOut:
    product = await session.get(Product, body.productId)
    if product is None or product.status != "active":
        raise BusinessError("商品不存在或已下架")

    receiver = await address_service.resolve_receiver(
        session, user, address_id=body.addressId, receiver=body.receiver
    )

    line_cents = product.price_cents * body.qty
    freight_cents = 0
    pay_cents = line_cents + freight_cents
    now = now_cn()
    order_no = await generate_order_no(session)

    order = Order(
        order_no=order_no,
        user_id=user.id,
        status=OrderStatus.PENDING_PAYMENT,
        product_amount_cents=line_cents,
        freight_amount_cents=freight_cents,
        pay_amount_cents=pay_cents,
        remark=body.remark,
        receiver_name=receiver.name,
        receiver_phone=receiver.phone,
        receiver_address=receiver.full_address(),
        expire_at=now + timedelta(hours=settings.order_expire_hours),
    )
    session.add(order)
    await session.flush()

    session.add(
        OrderItem(
            order_id=order.id,
            product_id=product.id,
            title=product.title,
            thumb=product.cover_url,
            unit_price_cents=product.price_cents,
            qty=body.qty,
            line_amount_cents=line_cents,
        )
    )
    await _log_status(
        session, order, None, OrderStatus.PENDING_PAYMENT, "user", user.user_no, "用户提交订单"
    )
    await session.commit()

    order = await _load_order(session, order.order_no, user.id)
    return order_to_detail(order)


async def pay_mock(session: AsyncSession, user: User, order_no: str) -> PayMockOut:
    order = await _load_order(session, order_no, user.id)
    if order.status == OrderStatus.PENDING_SHIPPING:
        return PayMockOut(
            orderNo=order.order_no,
            status=order.status,
            payAmount=cents_to_yuan(order.pay_amount_cents),
        )
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise BusinessError("当前订单状态不可支付")

    if order.expire_at and now_cn() > order.expire_at:
        raise BusinessError("订单已超时，请重新下单")

    now = now_cn()
    prev = order.status
    order.status = OrderStatus.PENDING_SHIPPING
    order.payment_method = "wechat_mock"
    order.paid_at = now
    await _log_status(session, order, prev, order.status, "user", user.user_no, "假支付成功")
    await session.commit()

    return PayMockOut(
        orderNo=order.order_no,
        status=order.status,
        payAmount=cents_to_yuan(order.pay_amount_cents),
    )


async def cancel_order(session: AsyncSession, user: User, order_no: str) -> None:
    order = await _load_order(session, order_no, user.id)
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise BusinessError("仅待付款订单可取消")
    prev = order.status
    order.status = OrderStatus.CLOSED
    order.closed_at = now_cn()
    await _log_status(session, order, prev, order.status, "user", user.user_no, "用户取消订单")
    await session.commit()


def _resolve_status_filter(tab: str) -> Optional[str]:
    mapping = {
        "待付款": OrderStatus.PENDING_PAYMENT,
        "pending_payment": OrderStatus.PENDING_PAYMENT,
        "待发货": OrderStatus.PENDING_SHIPPING,
        "pending_shipping": OrderStatus.PENDING_SHIPPING,
        "已发货": OrderStatus.SHIPPED,
        "shipped": OrderStatus.SHIPPED,
        "已完成": OrderStatus.COMPLETED,
        "completed": OrderStatus.COMPLETED,
        "已关闭": OrderStatus.CLOSED,
        "closed": OrderStatus.CLOSED,
        "已退款": OrderStatus.REFUNDED,
        "refunded": OrderStatus.REFUNDED,
        "退款审核中": OrderStatus.REFUND_PENDING,
        "refund_pending": OrderStatus.REFUND_PENDING,
        "售后": OrderStatus.REFUND_PENDING,
    }
    if tab in mapping:
        return mapping[tab]
    for code, label in ORDER_STATUS_LABEL.items():
        if tab == code or tab == label:
            return code
    return None


async def list_orders(
    session: AsyncSession,
    user: User,
    *,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> List[OrderListItemOut]:
    from app.models.refund import Refund

    q = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items), selectinload(Order.refund))
        .order_by(Order.created_at.desc())
    )
    if status:
        tab = status.strip()
        if tab in ("售后", "after_sale"):
            q = q.where(
                Order.status.in_([OrderStatus.REFUNDED, OrderStatus.REFUND_PENDING])
            )
        else:
            code = _resolve_status_filter(tab)
            if code:
                q = q.where(Order.status == code)

    offset = max(page - 1, 0) * page_size
    result = await session.execute(q.offset(offset).limit(min(page_size, 100)))
    return [order_to_list_item(o) for o in result.scalars().unique().all()]


async def get_order_detail(session: AsyncSession, user: User, order_no: str) -> OrderDetailOut:
    order = await _load_order(session, order_no, user.id)
    return order_to_detail(order)


async def ship_order(
    session: AsyncSession, order_no: str, carrier: str, tracking_no: str
) -> OrderDetailOut:
    order = await _load_order(session, order_no)
    if order.status == OrderStatus.SHIPPED:
        return order_to_detail(order, mask_receiver_phone=False)
    if order.status == OrderStatus.REFUND_PENDING:
        raise BusinessError("订单退款审核中，暂不可发货")
    if order.status != OrderStatus.PENDING_SHIPPING:
        raise BusinessError("仅待发货订单可发货")

    now = now_cn()
    prev = order.status
    order.status = OrderStatus.SHIPPED
    order.shipped_at = now
    session.add(
        Shipment(order_id=order.id, carrier=carrier, tracking_no=tracking_no, shipped_at=now)
    )
    await _log_status(
        session, order, prev, order.status, "admin", None, f"{carrier} {tracking_no}"
    )
    await session.commit()
    order = await _load_order(session, order_no)
    return order_to_detail(order, mask_receiver_phone=False)


async def close_expired_orders(session: AsyncSession) -> int:
    now = now_cn()
    result = await session.execute(
        select(Order).where(
            Order.status == OrderStatus.PENDING_PAYMENT,
            Order.expire_at.is_not(None),
            Order.expire_at < now,
        )
    )
    orders = result.scalars().all()
    count = 0
    for order in orders:
        prev = order.status
        order.status = OrderStatus.CLOSED
        order.closed_at = now
        await _log_status(session, order, prev, order.status, "system", None, "支付超时自动关闭")
        count += 1
    if count:
        await session.commit()
    return count


async def auto_complete_shipped_orders(session: AsyncSession) -> int:
    cutoff = now_cn() - timedelta(days=settings.auto_complete_shipped_days)
    result = await session.execute(
        select(Order).where(
            Order.status == OrderStatus.SHIPPED,
            Order.shipped_at.is_not(None),
            Order.shipped_at < cutoff,
        )
    )
    orders = result.scalars().all()
    count = 0
    for order in orders:
        prev = order.status
        order.status = OrderStatus.COMPLETED
        order.completed_at = now_cn()
        await _log_status(session, order, prev, order.status, "system", None, "自动确认收货")
        count += 1
    if count:
        await session.commit()
    return count
