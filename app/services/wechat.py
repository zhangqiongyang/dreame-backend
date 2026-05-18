from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BusinessError


async def code_to_session(code: str) -> dict[str, Any]:
    if settings.wechat_mock or not settings.wechat_appid or not settings.wechat_secret:
        return {
            "openid": f"mock_{code[:32]}",
            "session_key": "mock_session_key",
            "unionid": None,
        }

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if data.get("errcode"):
        raise BusinessError(data.get("errmsg", "微信登录失败"))

    if not data.get("openid"):
        raise BusinessError("微信登录码无效")

    return data
