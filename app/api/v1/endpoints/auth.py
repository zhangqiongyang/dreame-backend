from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.response import ApiResponse, success
from app.schemas.auth import PhoneBindIn, ProfileUpdateIn, WechatLoginIn, WechatLoginOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/wechat", response_model=ApiResponse[WechatLoginOut])
async def wechat_login(body: WechatLoginIn, db: DbSession) -> ApiResponse[WechatLoginOut]:
    data = await auth_service.login_by_wechat_code(db, body.code)
    return success(data)


@router.get("/me", response_model=ApiResponse)
async def me(user: CurrentUser) -> ApiResponse:
    return success(auth_service.user_to_out(user))


@router.patch("/profile", response_model=ApiResponse)
async def update_profile(body: ProfileUpdateIn, db: DbSession, user: CurrentUser) -> ApiResponse:
    data = await auth_service.update_profile(db, user, body)
    return success(data)


@router.post("/phone", response_model=ApiResponse)
async def bind_phone(body: PhoneBindIn, db: DbSession, user: CurrentUser) -> ApiResponse:
    data = await auth_service.bind_phone(db, user, body.code)
    return success(data)
