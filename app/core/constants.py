from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PENDING_SHIPPING = "pending_shipping"
    REFUND_PENDING = "refund_pending"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CLOSED = "closed"
    REFUNDED = "refunded"


ORDER_STATUS_LABEL: dict[str, str] = {
    OrderStatus.PENDING_PAYMENT: "待付款",
    OrderStatus.PENDING_SHIPPING: "待发货",
    OrderStatus.REFUND_PENDING: "退款审核中",
    OrderStatus.SHIPPED: "已发货",
    OrderStatus.COMPLETED: "已完成",
    OrderStatus.CLOSED: "已关闭",
    OrderStatus.REFUNDED: "已退款",
}


class RefundStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


REFUND_STATUS_LABEL: dict[str, str] = {
    RefundStatus.PENDING: "待审核",
    RefundStatus.APPROVED: "已通过",
    RefundStatus.REJECTED: "已拒绝",
}


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


PRODUCT_STATUS_LABEL: dict[str, str] = {
    ProductStatus.ACTIVE: "在售",
    ProductStatus.INACTIVE: "已下架",
}


REFUND_REASONS = [
    "多拍/错拍",
    "不想要了",
    "商品信息有误",
    "价格高于其他平台",
    "其他原因",
]
