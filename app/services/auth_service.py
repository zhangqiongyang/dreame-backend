from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import UserStatus
from app.core.exceptions import BusinessError, UnauthorizedError
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.schemas.auth import ProfileUpdateIn, UserOut, WechatLoginOut
from app.services import wechat as wechat_client
from app.utils.datetime_util import utcnow


def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        nickname=user.nickname,
        avatarUrl=user.avatar_url,
        phone=user.phone,
    )


async def login_by_wechat_code(session: AsyncSession, code: str) -> WechatLoginOut:
    wx = await wechat_client.code_to_session(code)
    openid = wx["openid"]

    result = await session.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    now = utcnow()

    if user is None:
        user = User(
            openid=openid,
            unionid=wx.get("unionid"),
            session_key=wx.get("session_key"),
            status=UserStatus.ACTIVE,
            last_login_at=now,
        )
        session.add(user)
    else:
        if user.status == UserStatus.DISABLED:
            raise BusinessError("账号已被禁用")
        user.session_key = wx.get("session_key")
        user.unionid = wx.get("unionid") or user.unionid
        user.last_login_at = now

    await session.commit()
    await session.refresh(user)

    token = create_access_token(str(user.id))
    return WechatLoginOut(
        token=token,
        expiresIn=settings.jwt_expire_seconds,
        user=user_to_out(user),
    )


async def get_user_from_token(session: AsyncSession, token: str) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception as exc:
        raise UnauthorizedError() from exc

    user = await session.get(User, user_id)
    if user is None or user.status == UserStatus.DISABLED:
        raise UnauthorizedError()
    return user


async def update_profile(session: AsyncSession, user: User, body: ProfileUpdateIn) -> UserOut:
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatarUrl is not None:
        user.avatar_url = body.avatarUrl
    await session.commit()
    await session.refresh(user)
    return user_to_out(user)
