import asyncio
import logging

from app.db.session import get_session
from app.services import order_service

logger = logging.getLogger(__name__)


async def run_order_maintenance_once() -> None:
    async for session in get_session():
        closed = await order_service.close_expired_orders(session)
        completed = await order_service.auto_complete_shipped_orders(session)
        if closed or completed:
            logger.info("order maintenance: closed=%s completed=%s", closed, completed)
        break


async def order_maintenance_loop(stop_event: asyncio.Event, interval_seconds: int = 300) -> None:
    while not stop_event.is_set():
        try:
            await run_order_maintenance_once()
        except Exception:
            logger.exception("order maintenance failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue
