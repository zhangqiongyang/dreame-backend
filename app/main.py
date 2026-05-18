import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import BusinessError, UnauthorizedError
from app.core.response import fail
from app.tasks.order_expire import order_maintenance_loop

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
