from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import UserStatus
from app.core.exceptions import BusinessError, UnauthorizedError
from app.core.security import create_access_token, decode_access_token
from app.models.user import User
from app.schemas.auth import ProfileUpdateIn, UserOut, WechatLoginOut
from app.services import wechat as wechat_client
from app.services.wechat import is_wechat_mock_mode
from app.utils.datetime_util import now_cn
from app.utils.ids import IdPrefix, generate_unique_id, is_valid_business_id

logger = logging.getLogger(__name__)
def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.user_no,
        nickname=user.nickname,
        avatarUrl=user.avatar_url,
        phone=user.phone,
    )


async def _allocate_user_no(session: AsyncSession) -> str:
    async def exists(no: str) -> bool:
        r = await session.execute(select(User.id).where(User.user_no == no).limit(1))
        return r.scalar_one_or_none() is not None

    return await generate_unique_id(session, IdPrefix.USER, exists_query=exists)


async def _inherit_phone_from_unionid_sibling(
    session: AsyncSession, user: User, unionid: Optional[str]
) -> None:
    """同一微信 unionid 下若存在已绑手机的历史账号，登录时同步到当前 openid 账号。"""
    if user.phone or not unionid:
        return
    result = await session.execute(
        select(User)
        .where(
            User.unionid == unionid,
            User.id != user.id,
            User.phone.is_not(None),
        )
        .order_by(User.last_login_at.desc())
        .limit(1)
    )
    sibling = result.scalar_one_or_none()
    if not sibling or not sibling.phone:
        return
    user.phone = sibling.phone
    sibling.phone = None
    logger.info(
        "登录同步手机号: from_user=%s to_user=%s phone=%s…",
        sibling.user_no,
        user.user_no,
        sibling.phone[:3],
    )


async def login_by_wechat_code(session: AsyncSession, code: str) -> WechatLoginOut:
    wx = await wechat_client.code_to_session(code)
    openid = wx["openid"]
    if not is_wechat_mock_mode() and str(openid).startswith("mock_"):
        raise BusinessError("微信登录异常，请检查后端 AppID/Secret 配置")

    result = await session.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()
    now = now_cn()

    if user is None:
        user = User(
            user_no=await _allocate_user_no(session),
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

    unionid = wx.get("unionid") or user.unionid
    await _inherit_phone_from_unionid_sibling(session, user, unionid)

    await session.commit()
    await session.refresh(user)

    token = create_access_token(user.user_no)
    return WechatLoginOut(
        token=token,
        expiresIn=settings.jwt_expire_seconds,
        user=user_to_out(user),
    )


async def get_user_from_token(session: AsyncSession, token: str) -> User:
    try:
        payload = decode_access_token(token)
        sub = payload["sub"]
    except Exception as exc:
        raise UnauthorizedError() from exc

    user: Optional[User] = None
    if isinstance(sub, str) and is_valid_business_id(sub, IdPrefix.USER):
        result = await session.execute(select(User).where(User.user_no == sub))
        user = result.scalar_one_or_none()
    else:
        try:
            user = await session.get(User, int(sub))
        except (TypeError, ValueError):
            user = None

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


async def bind_phone(session: AsyncSession, user: User, code: str) -> UserOut:
    phone = await wechat_client.get_phone_number(code)

    if user.phone == phone:
        return user_to_out(user)

    result = await session.execute(
        select(User).where(User.phone == phone, User.id != user.id).limit(1)
    )
    other = result.scalar_one_or_none()
    if other:
        # 微信 getPhoneNumber 已验证归属，从旧 openid 账号收回手机号
        logger.info(
            "手机号迁移: from_user=%s(openid=%s…) to_user=%s phone=%s…",
            other.user_no,
            str(other.openid)[:8],
            user.user_no,
            phone[:3],
        )
        other.phone = None
        await session.flush()

    user.phone = phone
    await session.commit()
    await session.refresh(user)
    return user_to_out(user)
