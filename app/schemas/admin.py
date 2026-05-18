from typing import Optional

from pydantic import BaseModel, Field


class AdminLoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class AdminUserOut(BaseModel):
    username: str
    displayName: str
    role: str


class AdminLoginOut(BaseModel):
    token: str
    expiresIn: int
    user: AdminUserOut


class DashboardOut(BaseModel):
    todayOrders: int
    todaySales: int
    pendingShipCount: int
    newUsers: int


class AdminOrderRowOut(BaseModel):
    id: str
    orderNo: str
    user: str
    amount: int
    status: str
    createdAt: str


class ShipOrderIn(BaseModel):
    carrier: str = Field(min_length=1, max_length=64)
    trackingNo: str = Field(min_length=1, max_length=64)


class RefundAuditIn(BaseModel):
    auditRemark: Optional[str] = Field(default=None, max_length=500)


class AdminRefundRowOut(BaseModel):
    id: str
    refundNo: str
    orderNo: str
    user: str
    amount: int
    reason: str
    status: str


class AdminUserRowOut(BaseModel):
    id: str
    name: str
    phone: str
    orders: int
    spent: int


class UserStatusIn(BaseModel):
    status: str = Field(pattern="^(active|disabled)$")
