"""Enterprise RBAC engine with role inheritance."""

from app.iam.permissions.catalog import SYSTEM_ROLE_INHERITANCE, SYSTEM_ROLE_PERMISSIONS


class RbacEngine:
    """Resolves effective permissions for a role slug, including inheritance."""

    def resolve_permissions(
        self,
        role_slug: str,
        *,
        custom_permissions: list[str] | None = None,
        inherits_from: list[str] | None = None,
    ) -> set[str]:
        perms: set[str] = set(custom_permissions or [])
        perms |= self._system_permissions(role_slug)
        for parent in inherits_from or SYSTEM_ROLE_INHERITANCE.get(role_slug, []):
            perms |= self._system_permissions(parent)
        return perms

    def has_permission(
        self,
        role_slug: str,
        permission: str,
        *,
        custom_permissions: list[str] | None = None,
        extra_permissions: list[str] | None = None,
    ) -> bool:
        effective = self.resolve_permissions(role_slug, custom_permissions=custom_permissions)
        if extra_permissions:
            effective |= set(extra_permissions)
        return permission in effective

    def _system_permissions(self, role_slug: str) -> set[str]:
        return set(SYSTEM_ROLE_PERMISSIONS.get(role_slug, frozenset()))
