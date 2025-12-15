from __future__ import annotations

import asyncio
import logging
from typing import Optional

from sqlmodel import Session

from app.config import get_settings
from app.db import get_engine
from app.services import recurring_template_service

logger = logging.getLogger(__name__)


class RecurringTemplateScheduler:
    """Background loop that checks recurring request templates."""

    def __init__(self, *, poll_seconds: int | None = None):
        settings = get_settings()
        raw_interval = poll_seconds or settings.recurring_template_poll_seconds
        # Never poll faster than every 30 seconds to avoid hot loops
        self._poll_seconds = max(30, raw_interval)
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_running_loop()
        self._stop_event.clear()
        self._task = loop.create_task(self._run_loop())
        logger.info("Recurring template scheduler started (interval=%s seconds)", self._poll_seconds)

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._stop_event = asyncio.Event()
            logger.info("Recurring template scheduler stopped")

    async def _run_loop(self) -> None:
        try:
            while not self._stop_event.is_set():
                await self._run_tick()
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_seconds)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            logger.debug("Recurring template scheduler cancelled")
            raise
        except Exception:  # pragma: no cover - safety net
            logger.exception("Recurring template scheduler crashed")

    async def _run_tick(self) -> None:
        try:
            with Session(get_engine()) as session:
                due_templates = recurring_template_service.list_due_templates(session)
                if due_templates:
                    logger.info(
                        "Recurring template scheduler found %s due template(s)",
                        len(due_templates),
                    )
                else:
                    logger.debug("Recurring template scheduler tick: no due templates")
        except Exception:
            logger.exception("Recurring template scheduler tick failed")


def install_recurring_scheduler(app) -> None:
    scheduler = RecurringTemplateScheduler()
    app.state.recurring_template_scheduler = scheduler

    @app.on_event("startup")
    async def _start_scheduler() -> None:  # pragma: no cover - lifecycle hook
        scheduler.start()

    @app.on_event("shutdown")
    async def _stop_scheduler() -> None:  # pragma: no cover - lifecycle hook
        await scheduler.stop()
