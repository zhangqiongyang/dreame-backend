from typing import List, Optional

from pydantic import BaseModel, Field


class RefundEligibilityOut(BaseModel):
    canApply: bool
    message: str
    refundAmount: Optional[int] = None


class CreateRefundIn(BaseModel):
    reason: str = Field(min_length=1, max_length=64)
    reasonText: Optional[str] = Field(default=None, max_length=500)


class RefundStepOut(BaseModel):
    title: str
    time: Optional[str]
    remark: Optional[str]
    done: bool
    active: bool


class RefundDetailOut(BaseModel):
    id: str
    refundNo: str
    orderId: str
    status: str
    statusLabel: str
    amount: int
    reason: str
    reasonText: Optional[str]
    steps: List[RefundStepOut]
