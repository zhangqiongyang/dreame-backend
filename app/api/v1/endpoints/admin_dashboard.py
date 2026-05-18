from fastapi import APIRouter, Depends

from app.api.deps import DbSession, verify_admin
from app.core.response import ApiResponse, success
from app.schemas.admin import DashboardOut
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin)])


@router.get("/dashboard", response_model=ApiResponse[DashboardOut])
async def dashboard(db: DbSession) -> ApiResponse[DashboardOut]:
    return success(await admin_service.get_dashboard(db))
