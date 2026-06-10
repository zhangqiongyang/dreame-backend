import asyncio
import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import _ENV_FILE, settings
from app.core.logging_config import setup_logging
from app.services.wechat import is_wechat_mock_mode, wechat_mock_reason
from app.core.exceptions import BusinessError, UnauthorizedError
from app.core.response import fail
from app.tasks.order_expire import order_maintenance_loop

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

_wechat_mode_label: str = ""


def _resolve_wechat_mode() -> str:
    if is_wechat_mock_mode():
        return "mock"
    return "production"


def _log_wechat_mode() -> None:
    global _wechat_mode_label
    mode = _resolve_wechat_mode()
    _wechat_mode_label = mode
    env_hint = f"env={_ENV_FILE} exists={_ENV_FILE.is_file()}"
    if mode == "mock":
        reason = wechat_mock_reason()
        msg = f"微信登录: Mock 模式（{reason}）| {env_hint}"
        logger.warning(msg)
        print(msg, flush=True)
    else:
        msg = f"微信登录: 正式模式 appid={settings.wechat_appid[:8]}… | {env_hint}"
        logger.info(msg)
        print(msg, flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_wechat_mode()
    stop_event = asyncio.Event()
    task = None
    if settings.database_url:
        task = asyncio.create_task(order_maintenance_loop(stop_event))
    yield
    stop_event.set()
    if task:
        await task


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validation_error_message(exc: RequestValidationError) -> str:
    for err in exc.errors():
        msg = str(err.get("msg", ""))
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        if msg:
            return msg
    return "参数校验失败"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    body = fail(_validation_error_message(exc))
    return JSONResponse(status_code=200, content=body.model_dump())


@app.exception_handler(BusinessError)
async def business_error_handler(_: Request, exc: BusinessError) -> JSONResponse:
    body = fail(exc.message)
    return JSONResponse(status_code=exc.http_status, content=body.model_dump())


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_: Request, exc: UnauthorizedError) -> JSONResponse:
    body = fail(exc.message)
    return JSONResponse(status_code=exc.http_status, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error: %s", exc)
    body = fail("服务器内部错误")
    return JSONResponse(status_code=500, content=body.model_dump())


app.include_router(api_router, prefix="/api/v1")

_upload_root = settings.upload_dir
if not Path(_upload_root).is_absolute():
    _upload_root = settings.backend_root / _upload_root
Path(_upload_root).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_root)), name="uploads")


@app.get("/health")
async def health() -> dict:
    mode = _wechat_mode_label or _resolve_wechat_mode()
    return {
        "status": "ok",
        "wechatLogin": mode,
        "wechatAppId": settings.wechat_appid[:8] + "…" if settings.wechat_appid else "",
    }
