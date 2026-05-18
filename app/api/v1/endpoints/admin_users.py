from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, verify_admin
from app.core.response import ApiResponse, success
from app.schemas.admin import AdminUserRowOut, UserStatusIn
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin-users"], dependencies=[Depends(verify_admin)])


@router.get("/users", response_model=ApiResponse[list[AdminUserRowOut]])
async def list_users(
    db: DbSession,
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[list[AdminUserRowOut]]:
    return success(
        await admin_service.list_users(db, keyword=keyword, page=page, page_size=pageSize)
    )


@router.patch("/users/{user_id}/status", response_model=ApiResponse)
async def update_user_status(user_id: int, body: UserStatusIn, db: DbSession) -> ApiResponse:
    await admin_service.set_user_status(db, user_id, body.status)
    return success()
