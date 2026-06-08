import logging
import time
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import BusinessError
from app.utils.phone import validate_cn_mobile

logger = logging.getLogger(__name__)

_access_token: Optional[str] = None
_access_token_expires_at: float = 0.0

MOCK_OPENID = "mock_dev_user"
MOCK_PHONE = "13800138000"

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
            "openid": MOCK_OPENID,
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


async def get_access_token() -> str:
    global _access_token, _access_token_expires_at

    if is_wechat_mock_mode():
        return "mock_access_token"

    now = time.time()
    if _access_token and now < _access_token_expires_at - 60:
        return _access_token

    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": settings.wechat_appid.strip(),
        "secret": settings.wechat_secret.strip(),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if data.get("errcode"):
        errcode = int(data.get("errcode", 0))
        msg = data.get("errmsg") or "获取微信 access_token 失败"
        logger.warning("微信 access_token 失败 errcode=%s errmsg=%s", errcode, msg)
        raise BusinessError("微信服务暂不可用，请稍后再试")

    token = data.get("access_token")
    if not token:
        raise BusinessError("获取微信 access_token 失败")

    _access_token = str(token)
    _access_token_expires_at = now + float(data.get("expires_in", 7200))
    return _access_token


def _mock_phone_from_code(code: str) -> str:
    del code
    return MOCK_PHONE


async def get_phone_number(code: str) -> str:
    """消费 getPhoneNumber 组件返回的 code，换取用户手机号。"""
    if is_wechat_mock_mode():
        logger.warning("手机号绑定使用 Mock 模式")
        return validate_cn_mobile(_mock_phone_from_code(code))

    access_token = await get_access_token()
    url = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"
    params = {"access_token": access_token}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, params=params, json={"code": code})
        data = resp.json()

    if data.get("errcode"):
        errcode = int(data.get("errcode", 0))
        hint = _WX_ERR_HINT.get(errcode)
        msg = hint or data.get("errmsg") or "获取手机号失败"
        logger.warning("微信 getuserphonenumber 失败 errcode=%s errmsg=%s", errcode, data.get("errmsg"))
        raise BusinessError(msg)

    phone_info = data.get("phone_info") or {}
    raw = phone_info.get("purePhoneNumber") or phone_info.get("phoneNumber")
    if not raw:
        raise BusinessError("未获取到手机号")

    try:
        return validate_cn_mobile(str(raw))
    except ValueError as exc:
        raise BusinessError(str(exc)) from exc
