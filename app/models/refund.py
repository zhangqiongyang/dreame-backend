from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    refund_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.user_no"), index=True, nullable=False
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    audit_remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="refund")  # noqa: F821
    status_logs: Mapped[List["RefundStatusLog"]] = relationship(
        back_populates="refund", cascade="all, delete-orphan"
    )


class RefundStatusLog(Base):
    __tablename__ = "refund_status_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    refund_id: Mapped[int] = mapped_column(ForeignKey("refunds.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    refund: Mapped["Refund"] = relationship(back_populates="status_logs")
