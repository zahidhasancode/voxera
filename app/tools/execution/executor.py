"""Tool execution orchestration with retry, timeout, and circuit breaker."""

import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.exceptions import ToolCircuitOpenError, ToolExecutionError
from app.tools.execution.circuit_breaker import CircuitBreakerRegistry
from app.tools.execution.retry import RetryStrategy
from app.tools.execution.timeout import with_timeout
from app.tools.interfaces.tool import Tool
from app.tools.schemas.execution import ToolExecutionContext


class ToolExecutor:
    def __init__(
        self,
        *,
        retry: RetryStrategy | None = None,
        circuit_registry: CircuitBreakerRegistry | None = None,
    ) -> None:
        self._retry = retry or RetryStrategy()
        self._circuits = circuit_registry or CircuitBreakerRegistry()

    async def run(
        self,
        tool: Tool,
        context: ToolExecutionContext,
    ) -> tuple[dict[str, Any], float, int]:
        circuit_key = f"{context.tenant_id}:{context.tool_slug}"
        breaker = self._circuits.get(circuit_key)
        breaker.allow()

        start = time.perf_counter()

        async def _execute() -> dict[str, Any]:
            return await with_timeout(
                lambda: tool.execute(context),
                timeout_seconds=context.timeout_seconds,
            )

        try:
            result, retry_count = await self._retry.execute(_execute)
            breaker.record_success()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return result, elapsed_ms, retry_count
        except ToolCircuitOpenError:
            raise
        except Exception:
            breaker.record_failure()
            raise
