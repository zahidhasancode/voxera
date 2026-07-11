"""RBAC engine tests."""

from app.core.enums import IamPermission, SystemRole
from app.iam.authorization.rbac_engine import RbacEngine


def test_owner_has_all_permissions():
    engine = RbacEngine()
    perms = engine.resolve_permissions(SystemRole.OWNER)
    assert IamPermission.MANAGE_ORGANIZATION in perms
    assert IamPermission.MANAGE_API_KEYS in perms


def test_viewer_limited_permissions():
    engine = RbacEngine()
    assert engine.has_permission(SystemRole.VIEWER, IamPermission.VIEW_CALLS)
    assert not engine.has_permission(SystemRole.VIEWER, IamPermission.MANAGE_USERS)


def test_developer_can_manage_api_keys():
    engine = RbacEngine()
    assert engine.has_permission(SystemRole.DEVELOPER, IamPermission.MANAGE_API_KEYS)
    assert not engine.has_permission(SystemRole.DEVELOPER, IamPermission.MANAGE_BILLING)


def test_custom_permissions_merged():
    engine = RbacEngine()
    assert engine.has_permission(
        SystemRole.VIEWER,
        IamPermission.DELETE_CALLS,
        custom_permissions=[IamPermission.DELETE_CALLS],
    )
