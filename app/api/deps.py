from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models.user import User
from app.services import auth_service

DbSession = Annotated[AsyncSession, Depends(get_session)]


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    return authorization[7:].strip()


async def get_current_user(
    db: DbSession,
    authorization: Annotated[Optional[str], Header()] = None,
) -> User:
    token = _extract_bearer(authorization)
    return await auth_service.get_user_from_token(db, token)


async def get_optional_user(
    db: DbSession,
    authorization: Annotated[Optional[str], Header()] = None,
) -> Optional[User]:
    if not authorization:
        return None
    try:
        token = _extract_bearer(authorization)
        return await auth_service.get_user_from_token(db, token)
    except UnauthorizedError:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]


def verify_admin(authorization: Annotated[Optional[str], Header()] = None) -> None:
    token = _extract_bearer(authorization)
    if token == settings.admin_token:
        return
    try:
        payload = decode_access_token(token)
        if payload.get("sub") == "admin" and payload.get("role") == "admin":
            return
    except Exception:
        pass
    raise UnauthorizedError("无管理权限，请重新登录")
