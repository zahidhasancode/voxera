"""Health and readiness dependency checks."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.core.observability import platform_metrics
from app.database.session import get_engine, get_session_factory
from app.streaming.metrics import streaming_metrics

APP_VERSION = "0.1.0"


async def check_database() -> dict[str, Any]:
    if not settings.database_enabled:
        return {"status": "skipped", "message": "DATABASE_URL not configured"}
    factory = get_session_factory()
    if factory is None:
        return {"status": "unhealthy", "message": "Session factory not initialized"}
    started = time.perf_counter()
    try:
        async with factory() as session:
            await session.execute(text("SELECT 1"))
            migration = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            version = migration.scalar_one_or_none()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "migration_version": version,
        }
    except Exception as exc:
        platform_metrics.record_dependency_failure("database")
        return {"status": "unhealthy", "message": str(exc)}






def check_streaming() -> dict[str, Any]:
    degraded = streaming_metrics.dropped_frames > 0 or streaming_metrics.current_latency_ms >= 100.0
    return {
        "status": "degraded" if degraded else "healthy",
        "current_latency_ms": round(streaming_metrics.current_latency_ms, 2),
        "max_latency_ms": round(streaming_metrics.max_latency_ms, 2),
        "dropped_frames": streaming_metrics.dropped_frames,
        "queue_depth": streaming_metrics.queue_depth,
    }


def check_redis_future() -> dict[str, Any]:
    return {"status": "skipped", "message": "Redis not configured (future)"}


def check_queue_future() -> dict[str, Any]:
    return {"status": "skipped", "message": "Queue service not configured (future)"}


def _aggregate_status(checks: dict[str, Any]) -> str:
    statuses = []
    for value in checks.values():
        if isinstance(value, dict) and "status" in value:
            statuses.append(value["status"])
        elif isinstance(value, dict):
            statuses.extend(v.get("status", "healthy") for v in value.values() if isinstance(v, dict))
    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    if any(s == "degraded" for s in statuses):
        return "degraded"
    return "healthy"


async def live_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "pid": os.getpid(),
    }


async def ready_check() -> dict[str, Any]:
    if settings.database_enabled and get_engine() is None:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {"database": {"status": "unhealthy", "message": "Engine not initialized"}},
        }

    checks = {
        "database": await check_database(),
        "redis": check_redis_future(),
        "queue": check_queue_future(),
    }
    status = _aggregate_status(checks)
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }


async def deep_check() -> dict[str, Any]:
    ready = await ready_check()
    ready["streaming"] = check_streaming()
    ready["platform_metrics"] = platform_metrics.snapshot()
    ready["checks"]["streaming"] = ready["streaming"]
    ready["status"] = _aggregate_status({**ready["checks"], "streaming": ready["streaming"]})
    return ready
