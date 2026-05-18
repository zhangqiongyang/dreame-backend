import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BusinessError

logger = logging.getLogger(__name__)

_WX_ERR_HINT = {
    40029: "登录码无效或已过期，请重新打开小程序",
    40163: "登录码已被使用，请重试",
    40226: "高风险用户，无法登录",
    -1: "微信服务繁忙，请稍后再试",
}


def is_wechat_mock_mode() -> bool:
    appid = (settings.wechat_appid or "").strip()
    secret = (settings.wechat_secret or "").strip()
    if settings.wechat_mock:
        return True
    if not appid or not secret:
        return True
    return False


def wechat_mock_reason() -> str:
    if settings.wechat_mock:
        return "WECHAT_MOCK=true"
    if not (settings.wechat_appid or "").strip():
        return "WECHAT_APPID 为空"
    if not (settings.wechat_secret or "").strip():
        return "WECHAT_SECRET 为空"
    return ""


async def code_to_session(code: str) -> dict[str, Any]:
    if is_wechat_mock_mode():
        reason = wechat_mock_reason()
        logger.warning("微信登录使用 Mock 模式: %s", reason)
        return {
            "openid": f"mock_{code[:32]}",
            "session_key": "mock_session_key",
            "unionid": None,
        }

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid.strip(),
        "secret": settings.wechat_secret.strip(),
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
        logger.warning("微信 jscode2session 失败 errcode=%s errmsg=%s", errcode, data.get("errmsg"))
        raise BusinessError(msg)

    if not data.get("openid"):
        raise BusinessError("微信登录码无效")

    openid = str(data["openid"])
    logger.info("微信登录成功 openid=%s…", openid[:8])
    return data
