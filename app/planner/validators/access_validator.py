"""Tenant isolation for planner operations."""

from uuid import UUID

from app.core.exceptions import CrossTenantPlannerError


class PlannerAccessValidator:
    def validate_scope(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        resource_tenant_id: UUID,
        resource_agent_id: UUID | None = None,
    ) -> None:
        if tenant_id != resource_tenant_id:
            raise CrossTenantPlannerError(
                f"Cross-tenant planner access denied: {tenant_id} != {resource_tenant_id}"
            )
        if resource_agent_id is not None and agent_id != resource_agent_id:
            raise CrossTenantPlannerError(
                f"Cross-agent planner access denied: {agent_id} != {resource_agent_id}"
            )
