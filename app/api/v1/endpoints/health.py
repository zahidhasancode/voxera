"""Health check endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.streaming.metrics import streaming_metrics

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    environment: str
    version: str
    streaming_status: Optional[str] = None
    current_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    dropped_frames: Optional[int] = None
    queue_depth: Optional[int] = None


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with streaming metrics."""
    response = HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.ENVIRONMENT,
        version="0.1.0",
    )

    # Add streaming metrics from singleton
    response.current_latency_ms = round(streaming_metrics.current_latency_ms, 2)
    response.max_latency_ms = round(streaming_metrics.max_latency_ms, 2)
    response.dropped_frames = streaming_metrics.dropped_frames
    response.queue_depth = streaming_metrics.queue_depth

    # Determine streaming status (OK if latency < 100ms, else DEGRADED)
    if streaming_metrics.dropped_frames > 0 or streaming_metrics.current_latency_ms >= 100.0:
        response.streaming_status = "DEGRADED"
    else:
        response.streaming_status = "OK"

    return response
