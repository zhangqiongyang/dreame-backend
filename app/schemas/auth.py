from typing import Optional

from pydantic import BaseModel, Field


class WechatLoginIn(BaseModel):
    code: str = Field(min_length=1)


class UserOut(BaseModel):
    id: str
    nickname: Optional[str]
    avatarUrl: Optional[str]
    phone: Optional[str]


class WechatLoginOut(BaseModel):
    token: str
    expiresIn: int
    user: UserOut


class ProfileUpdateIn(BaseModel):
    nickname: Optional[str] = None
    avatarUrl: Optional[str] = None
