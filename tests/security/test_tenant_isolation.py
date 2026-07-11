"""Multi-tenant isolation security tests."""

from __future__ import annotations

import pytest

from tests.fixtures.ids import TENANT_A, TENANT_B


@pytest.mark.security
@pytest.mark.asyncio
async def test_cross_tenant_path_is_protected(http_client):
    response = await http_client.get(f"/api/v1/tenants/{TENANT_A}/agents")
    assert response.status_code in (401, 403, 503)


@pytest.mark.security
@pytest.mark.asyncio
async def test_different_tenant_paths_equally_protected(http_client):
    for tenant in (TENANT_A, TENANT_B):
        response = await http_client.get(f"/api/v1/tenants/{tenant}/agents")
        assert response.status_code in (401, 403, 503)


@pytest.mark.security
def test_tenant_ids_are_distinct():
    assert TENANT_A != TENANT_B
