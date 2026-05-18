from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ReceiverIn


class CreateOrderIn(BaseModel):
    productId: str = Field(min_length=1)
    qty: int = Field(default=1, ge=1, le=99)
    remark: Optional[str] = Field(default=None, max_length=255)
    receiver: ReceiverIn


class OrderListItemOut(BaseModel):
    id: str
    orderNo: str
    status: str
    title: str
    qty: int
    amount: int
    thumb: str


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


class PayMockOut(BaseModel):
    orderNo: str
    status: str
    payAmount: int
