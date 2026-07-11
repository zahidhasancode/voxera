"""RBAC dependency tests."""

import pytest
from fastapi import HTTPException

from app.core.exceptions import InsufficientPermissionsError
from app.iam.api.deps import require_permissions
from app.iam.auth.principal import AuthenticatedPrincipal


@pytest.mark.asyncio
async def test_require_permissions_allows_when_present():
    principal = AuthenticatedPrincipal(
        user_id=None,
        organization_id=__import__("uuid").uuid4(),
        tenant_id=None,
        role_slug="developer",
        permissions=frozenset({"manage_agents", "execute_tools"}),
        auth_method="api_key",
    )
    checker = require_permissions("manage_agents")
    result = await checker(principal=principal)
    assert result is principal


@pytest.mark.asyncio
async def test_require_permissions_denies_when_missing():
    principal = AuthenticatedPrincipal(
        user_id=None,
        organization_id=__import__("uuid").uuid4(),
        tenant_id=None,
        role_slug="viewer",
        permissions=frozenset({"view_calls"}),
        auth_method="api_key",
    )
    checker = require_permissions("manage_organization")
    with pytest.raises(HTTPException) as exc:
        await checker(principal=principal)
    assert exc.value.status_code == 403
