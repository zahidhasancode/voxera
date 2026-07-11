"""Tenant isolation for verifier."""

from uuid import UUID

from app.core.exceptions import CrossTenantVerifierError


class VerifierAccessValidator:
    def validate_scope(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        resource_tenant_id: UUID,
        resource_agent_id: UUID | None = None,
    ) -> None:
        if tenant_id != resource_tenant_id:
            raise CrossTenantVerifierError(
                f"Cross-tenant verifier access denied: {tenant_id} != {resource_tenant_id}"
            )
        if resource_agent_id is not None and agent_id != resource_agent_id:
            raise CrossTenantVerifierError(
                f"Cross-agent verifier access denied: {agent_id} != {resource_agent_id}"
            )
