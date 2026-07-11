"""Retry strategy for external tool calls."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.config import settings
from app.core.exceptions import ToolExecutionError

T = TypeVar("T")


class RetryStrategy:
    def __init__(
        self,
        *,
        max_retries: int | None = None,
        base_delay_ms: int | None = None,
    ) -> None:
        self._max_retries = max_retries if max_retries is not None else settings.TOOL_MAX_RETRIES
        self._base_delay_ms = base_delay_ms if base_delay_ms is not None else settings.TOOL_RETRY_BASE_DELAY_MS

    async def execute(self, fn: Callable[[], Awaitable[T]]) -> tuple[T, int]:
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                result = await fn()
                return result, attempt
            except ToolExecutionError as exc:
                last_exc = exc
                if not exc.retryable or attempt >= self._max_retries:
                    raise
                delay = (self._base_delay_ms / 1000.0) * (2**attempt)
                await asyncio.sleep(delay)
            except Exception as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise ToolExecutionError(str(exc), retryable=False) from exc
                delay = (self._base_delay_ms / 1000.0) * (2**attempt)
                await asyncio.sleep(delay)
        raise ToolExecutionError(str(last_exc or "retry_exhausted"), retryable=False)
