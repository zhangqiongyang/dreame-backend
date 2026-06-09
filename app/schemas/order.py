from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ReceiverIn
from app.schemas.refund import OrderRefundOut


class CreateOrderIn(BaseModel):
    productId: str = Field(min_length=1)
    qty: int = Field(default=1, ge=1, le=99)
    remark: Optional[str] = Field(default=None, max_length=255)
    addressId: Optional[str] = Field(default=None, min_length=1)
    receiver: Optional[ReceiverIn] = None

    @model_validator(mode="after")
    def require_address_or_receiver(self) -> "CreateOrderIn":
        if not self.addressId and self.receiver is None:
            raise ValueError("请选择收货地址或填写收件信息")
        return self


class OrderListItemOut(BaseModel):
    id: str
    orderNo: str
    status: str
    title: str
    qty: int
    amount: int
    thumb: str
    spec: Optional[str] = None
    hot: bool = False


class ShipmentOut(BaseModel):
    carrier: str
    trackingNo: str


class OrderDetailOut(BaseModel):
    id: str
    orderNo: str
    status: str
    statusLabel: str
    title: str
    qty: int
    amount: int
    thumb: str
    remark: Optional[str]
    paymentMethod: Optional[str]
    createdAt: str
    paidAt: Optional[str]
    completedAt: Optional[str]
    receiverName: str
    receiverPhone: str
    receiverAddress: str
    productAmount: int
    freightAmount: int
    payAmount: int
    shipment: Optional[ShipmentOut] = None
    refundReason: Optional[str] = None
    refund: Optional[OrderRefundOut] = None


class PayMockOut(BaseModel):
    orderNo: str
    status: str
    payAmount: int
