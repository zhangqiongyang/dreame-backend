from fastapi import APIRouter, Depends

from app.api.deps import verify_admin
from app.core.response import ApiResponse, success
from app.schemas.admin import AdminLoginIn, AdminLoginOut, AdminUserOut
from app.services import admin_auth_service

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=ApiResponse[AdminLoginOut])
async def login(body: AdminLoginIn) -> ApiResponse[AdminLoginOut]:
    return success(admin_auth_service.admin_login(body))


@router.get("/me", response_model=ApiResponse[AdminUserOut], dependencies=[Depends(verify_admin)])
async def me() -> ApiResponse[AdminUserOut]:
    return success(admin_auth_service.admin_user_out())
