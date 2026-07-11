"""Health and readiness dependency checks."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.core.observability import platform_metrics
from app.database.session import get_engine, get_session_factory
from app.infrastructure.knowledge.providers import get_embedding_provider, get_vector_store
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


async def check_storage() -> dict[str, Any]:
    path = Path(settings.KNOWLEDGE_STORAGE_PATH)
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".healthcheck"
        test_file.write_text("ok")
        test_file.unlink(missing_ok=True)
        return {"status": "healthy", "path": str(path)}
    except Exception as exc:
        platform_metrics.record_dependency_failure("storage")
        return {"status": "unhealthy", "path": str(path), "message": str(exc)}


def check_embedding_provider() -> dict[str, Any]:
    provider_name = settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER
    if not provider_name:
        return {"status": "skipped", "message": "Not configured"}
    provider = get_embedding_provider()
    provider_type = type(provider).__name__
    if provider_type.startswith("Unconfigured"):
        return {
            "status": "degraded",
            "provider": provider_name,
            "implementation": provider_type,
            "message": "Provider configured but not implemented",
        }
    return {"status": "healthy", "provider": provider_name, "implementation": provider_type}


def check_vector_store() -> dict[str, Any]:
    store_name = settings.KNOWLEDGE_DEFAULT_VECTOR_STORE
    if not store_name:
        return {"status": "skipped", "message": "Not configured"}
    store = get_vector_store()
    store_type = type(store).__name__
    if store_type.startswith("Unconfigured"):
        return {
            "status": "degraded",
            "provider": store_name,
            "implementation": store_type,
            "message": "Vector store configured but not implemented",
        }
    return {"status": "healthy", "provider": store_name, "implementation": store_type}


def check_domain_modules() -> dict[str, dict[str, Any]]:
    """Verify enterprise domain modules are loadable without invoking business logic."""
    modules = {}
    for name in ("planner", "verifier", "workflow", "tools", "memory", "rag"):
        try:
            __import__(f"app.{name}")
            modules[name] = {"status": "healthy"}
        except Exception as exc:
            modules[name] = {"status": "unhealthy", "message": str(exc)}
            platform_metrics.record_dependency_failure(name)
    return modules


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
        "storage": await check_storage(),
        "embedding_provider": check_embedding_provider(),
        "vector_store": check_vector_store(),
        "redis": check_redis_future(),
        "queue": check_queue_future(),
        "domains": check_domain_modules(),
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
