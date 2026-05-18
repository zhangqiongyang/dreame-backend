from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_dashboard,
    admin_orders,
    admin_refunds,
    admin_users,
    auth,
    health,
    orders,
    products,
    refunds,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(refunds.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_orders.router)
api_router.include_router(admin_refunds.router)
api_router.include_router(admin_users.router)
