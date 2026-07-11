"""Graceful shutdown coordination."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class ShutdownManager:
    """Tracks in-flight requests and coordinates graceful shutdown."""

    def __init__(self) -> None:
        self._shutting_down = False
        self._active_requests = 0
        self._lock = asyncio.Lock()
        self._drain_event = asyncio.Event()
        self._drain_event.set()

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down

    @property
    def active_requests(self) -> int:
        return self._active_requests

    async def begin_request(self) -> None:
        async with self._lock:
            if self._shutting_down:
                raise RuntimeError("Server is shutting down")
            self._active_requests += 1
            self._drain_event.clear()

    async def end_request(self) -> None:
        async with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
            if self._active_requests == 0:
                self._drain_event.set()

    async def initiate_shutdown(self, *, drain_timeout_seconds: float = 30.0) -> None:
        self._shutting_down = True
        logger.info(
            "Graceful shutdown initiated",
            extra_fields={"active_requests": self._active_requests},
        )
        try:
            await asyncio.wait_for(self._drain_event.wait(), timeout=drain_timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(
                "Shutdown drain timeout — forcing close",
                extra_fields={"active_requests": self._active_requests},
            )

    async def close_websockets(self) -> None:
        try:
            from app.core.connection_manager import ws_connection_manager

            await ws_connection_manager.disconnect_all()
        except Exception as exc:
            logger.warning("WebSocket shutdown error", extra_fields={"error": str(exc)})


shutdown_manager = ShutdownManager()
