from fastapi import APIRouter

from app.api.v1.endpoints import (
    addresses,
    admin_auth,
    admin_dashboard,
    admin_orders,
    admin_products,
    admin_refunds,
    admin_upload,
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
api_router.include_router(addresses.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(refunds.router)
api_router.include_router(admin_auth.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_orders.router)
api_router.include_router(admin_products.router)
api_router.include_router(admin_refunds.router)
api_router.include_router(admin_upload.router)
api_router.include_router(admin_users.router)
