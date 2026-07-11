"""Permission catalog tests."""

from app.core.enums import SystemRole
from app.iam.permissions.catalog import PERMISSION_CATALOG, SYSTEM_ROLE_PERMISSIONS


def test_all_permissions_have_metadata():
    assert len(PERMISSION_CATALOG) >= 10
    for slug, meta in PERMISSION_CATALOG.items():
        assert "name" in meta
        assert "category" in meta


def test_system_roles_defined():
    for role in SystemRole:
        assert role in SYSTEM_ROLE_PERMISSIONS
