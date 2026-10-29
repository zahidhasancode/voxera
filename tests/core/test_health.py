"""Health check tests."""

import pytest

from app.core.health import _aggregate_status, check_streaming, live_check


@pytest.mark.asyncio
async def test_live_check_always_healthy():
    payload = await live_check()
    assert payload["status"] == "healthy"
    assert "version" in payload
    assert "pid" in payload


def test_streaming_check_reports_queue_state():
    result = check_streaming()
    assert result["status"] in {"healthy", "degraded"}
    assert {"current_latency_ms", "dropped_frames", "queue_depth"} <= result.keys()


def test_aggregate_status_takes_the_worst():
    assert _aggregate_status({"a": {"status": "healthy"}, "b": {"status": "skipped"}}) == "healthy"
    assert _aggregate_status({"a": {"status": "healthy"}, "b": {"status": "degraded"}}) == "degraded"
    assert _aggregate_status({"a": {"status": "degraded"}, "b": {"status": "unhealthy"}}) == "unhealthy"
