"""Retry strategy tests."""

import pytest

from app.core.exceptions import ToolExecutionError
from app.tools.execution.retry import RetryStrategy


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    strategy = RetryStrategy(max_retries=2, base_delay_ms=1)
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ToolExecutionError("transient", retryable=True)
        return {"ok": True}

    result, retry_count = await strategy.execute(flaky)
    assert result == {"ok": True}
    assert retry_count == 1


@pytest.mark.asyncio
async def test_retry_exhausted():
    strategy = RetryStrategy(max_retries=1, base_delay_ms=1)

    async def always_fail():
        raise ToolExecutionError("fail", retryable=True)

    with pytest.raises(ToolExecutionError):
        await strategy.execute(always_fail)
