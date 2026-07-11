"""Chaos engineering — graceful degradation."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_readiness_degraded_when_database_down(http_client):
    with patch("app.core.health.check_database", new=AsyncMock(return_value={"status": "unhealthy", "message": "down"})):
        response = await http_client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert body["status"] in ("degraded", "unhealthy", "critical")


@pytest.mark.chaos
@pytest.mark.asyncio
async def test_liveness_survives_dependency_failure(http_client):
    with patch("app.core.health.check_database", new=AsyncMock(return_value={"status": "unhealthy", "message": "down"})):
        response = await http_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.chaos
def test_circuit_breaker_opens_after_failures():
    from app.core.exceptions import ToolCircuitOpenError
    from app.tools.execution.circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=30)
    breaker.record_failure()
    breaker.record_failure()
    with pytest.raises(ToolCircuitOpenError):
        breaker.allow()
