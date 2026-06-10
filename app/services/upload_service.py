from __future__ import annotations

import secrets
from pathlib import Path
from typing import Optional

from fastapi import Request, UploadFile

from app.core.config import settings
from app.core.exceptions import BusinessError

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_MAX_BYTES = 5 * 1024 * 1024


def _upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = settings.backend_root / root
    products_dir = root / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    return products_dir


def _public_base(request: Optional[Request]) -> str:
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    if request is not None:
        return str(request.base_url).rstrip("/")
    return "http://127.0.0.1:8000"


async def save_product_image(file: UploadFile, request: Optional[Request] = None) -> str:
    if not file.filename:
        raise BusinessError("请选择图片文件")

    content_type = (file.content_type or "").lower()
    suffix = _ALLOWED_CONTENT_TYPES.get(content_type)
    if suffix is None:
        raise BusinessError("仅支持 JPG、PNG、WebP、GIF 图片")

    data = await file.read()
    if not data:
        raise BusinessError("图片文件为空")
    if len(data) > _MAX_BYTES:
        raise BusinessError("图片大小不能超过 5MB")

    filename = f"{secrets.token_hex(16)}{suffix}"
    target = _upload_root() / filename
    target.write_bytes(data)

    return f"{_public_base(request)}/uploads/products/{filename}"
