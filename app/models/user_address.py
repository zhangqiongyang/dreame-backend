from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UserAddress(Base, TimestampMixin):
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    province: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    district: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    detail: Mapped[str] = mapped_column(String(255), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="addresses")  # noqa: F821
