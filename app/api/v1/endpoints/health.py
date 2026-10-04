"""Health check endpoints — live, ready, and deep diagnostics."""

from typing import Any

from fastapi import APIRouter, Response, status

from app.core.health import deep_check, live_check, ready_check
from app.streaming.metrics import streaming_metrics

router = APIRouter()


def _http_status(check_status: str) -> int:
    if check_status == "healthy":
        return status.HTTP_200_OK
    if check_status == "degraded":
        return status.HTTP_200_OK
    return status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/live")
async def health_live() -> dict[str, Any]:
    """Liveness — process is running."""
    return await live_check()


@router.get("/ready")
async def health_ready(response: Response) -> dict[str, Any]:
    """Readiness — dependencies required to serve traffic."""
    payload = await ready_check()
    response.status_code = _http_status(payload["status"])
    return payload


@router.get("/deep")
async def health_deep(response: Response) -> dict[str, Any]:
    """Deep diagnostics — extended dependency and platform checks."""
    payload = await deep_check()
    response.status_code = _http_status(payload["status"])
    return payload


@router.get("")
async def health_check_legacy(response: Response) -> dict[str, Any]:
    """Legacy health endpoint — delegates to readiness semantics."""
    payload = await ready_check()
    payload["streaming_status"] = (
        "DEGRADED"
        if streaming_metrics.dropped_frames > 0 or streaming_metrics.current_latency_ms >= 100.0
        else "OK"
    )
    payload["current_latency_ms"] = round(streaming_metrics.current_latency_ms, 2)
    payload["max_latency_ms"] = round(streaming_metrics.max_latency_ms, 2)
    payload["dropped_frames"] = streaming_metrics.dropped_frames
    payload["queue_depth"] = streaming_metrics.queue_depth
    response.status_code = _http_status(payload["status"])
    return payload
