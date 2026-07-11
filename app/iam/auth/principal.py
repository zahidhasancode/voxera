"""Authenticated request principal."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Identity attached to an authenticated HTTP or WebSocket request."""

    user_id: UUID | None
    organization_id: UUID
    tenant_id: UUID | None
    role_slug: str | None
    permissions: frozenset[str]
    auth_method: str  # "jwt" | "api_key"
    session_id: UUID | None = None
    api_key_id: UUID | None = None

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


@dataclass(frozen=True)
class TenantContext:
    """Resolved tenant scope for enterprise APIs."""

    tenant_id: UUID
    organization_id: UUID
    principal: AuthenticatedPrincipal
    permissions: frozenset[str] = field(default_factory=frozenset)
