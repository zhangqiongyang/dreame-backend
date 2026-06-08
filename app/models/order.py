from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.user_no"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    product_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    freight_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pay_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    receiver_name: Mapped[str] = mapped_column(String(64), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(512), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(
        back_populates="orders",
        foreign_keys=[user_id],
    )  # noqa: F821
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    shipment: Mapped[Optional["Shipment"]] = relationship(back_populates="order", uselist=False)
    status_logs: Mapped[List["OrderStatusLog"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    refund: Mapped[Optional["Refund"]] = relationship(back_populates="order", uselist=False)  # noqa: F821


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    thumb: Mapped[str] = mapped_column(String(512), nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    line_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    carrier: Mapped[str] = mapped_column(String(64), nullable=False)
    tracking_no: Mapped[str] = mapped_column(String(64), nullable=False)
    shipped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="shipment")


class OrderStatusLog(Base):
    __tablename__ = "order_status_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    operator_type: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="status_logs")
