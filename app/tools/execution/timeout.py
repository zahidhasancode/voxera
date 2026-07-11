"""Timeout wrapper for tool execution."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.config import settings
from app.core.enums import ToolFrameworkExecutionStatus
from app.core.exceptions import ToolExecutionError

T = TypeVar("T")


async def with_timeout(
    fn: Callable[[], Awaitable[T]],
    *,
    timeout_seconds: float | None = None,
) -> T:
    timeout = timeout_seconds if timeout_seconds is not None else settings.TOOL_EXECUTION_TIMEOUT_SECONDS
    try:
        return await asyncio.wait_for(fn(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise ToolExecutionError(
            f"Tool execution timed out after {timeout}s",
            retryable=True,
        ) from exc


def timeout_status(exc: Exception) -> ToolFrameworkExecutionStatus:
    if isinstance(exc, ToolExecutionError) and "timed out" in str(exc).lower():
        return ToolFrameworkExecutionStatus.TIMEOUT
    return ToolFrameworkExecutionStatus.FAILED
