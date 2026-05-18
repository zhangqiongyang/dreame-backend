from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BusinessError


_WX_ERR_HINT = {
    40029: "登录码无效或已过期，请重新打开小程序",
    40163: "登录码已被使用，请重试",
    40226: "高风险用户，无法登录",
    -1: "微信服务繁忙，请稍后再试",
}


async def code_to_session(code: str) -> dict[str, Any]:
    use_mock = settings.wechat_mock or not settings.wechat_appid or not settings.wechat_secret
    if use_mock:
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
        errcode = int(data.get("errcode", 0))
        hint = _WX_ERR_HINT.get(errcode)
        msg = hint or data.get("errmsg") or "微信登录失败"
        raise BusinessError(msg)

    if not data.get("openid"):
        raise BusinessError("微信登录码无效")

    return data
