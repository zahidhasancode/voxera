"""Integration tests — public API contract."""

from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_live_contract(http_client):
    response = await http_client.get("/api/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_ready_contract(http_client):
    response = await http_client.get("/api/v1/health/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    assert "status" in body
    assert "checks" in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_prometheus_format(http_client):
    response = await http_client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "voxera_http_requests_total" in response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_route_requires_auth(http_client, tenant_id):
    response = await http_client.get(f"/api/v1/tenants/{tenant_id}/agents")
    assert response.status_code in (401, 403, 503)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_bearer_token_rejected(http_client, tenant_id):
    response = await http_client.get(
        f"/api/v1/tenants/{tenant_id}/agents",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert response.status_code in (401, 403, 503)
