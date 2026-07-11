"""Tenant access validation for tool operations."""

from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import CrossTenantToolError
from app.core.enums import ToolPermissionEffect
from app.tools.schemas.execution import ToolPermissionRead


class ToolAccessValidator:
    """Validates tenant/agent scope on every lookup."""

    def validate_scope(
        self,
        *,
        tenant_id: UUID,
        agent_id: UUID,
        resource_tenant_id: UUID,
        resource_agent_id: UUID | None = None,
    ) -> None:
        if tenant_id != resource_tenant_id:
            raise CrossTenantToolError(
                f"Cross-tenant tool access denied: {tenant_id} != {resource_tenant_id}"
            )
        if resource_agent_id is not None and agent_id != resource_agent_id:
            raise CrossTenantToolError(
                f"Cross-agent tool access denied: {agent_id} != {resource_agent_id}"
            )


class ToolPermissionEvaluator:
    """Evaluates allow/block rules, rate limits, and working hours."""

    def evaluate(
        self,
        *,
        tool_slug: str,
        permissions: list[ToolPermissionRead],
        department: str | None = None,
        role: str | None = None,
        executions_last_hour: int = 0,
        now: datetime | None = None,
    ) -> tuple[bool, list[str]]:
        now = now or datetime.now(timezone.utc)
        violations: list[str] = []

        applicable = [p for p in permissions if p.tool_slug == tool_slug or p.tool_slug == "*"]
        if not applicable:
            return True, []

        blocks = [p for p in applicable if p.effect == ToolPermissionEffect.BLOCK]
        for block in blocks:
            if self._matches_scope(block, department, role):
                violations.append(f"blocked_by_policy: {block.tool_slug}")
                return False, violations

        allows = [p for p in applicable if p.effect == ToolPermissionEffect.ALLOW]
        if allows:
            if not any(self._matches_scope(p, department, role) for p in allows):
                violations.append("not_in_allowed_scope")
                return False, violations

        for perm in applicable:
            if perm.max_executions_per_hour is not None:
                if executions_last_hour >= perm.max_executions_per_hour:
                    violations.append("max_executions_per_hour_exceeded")
                    return False, violations

            if perm.working_hours_start and perm.working_hours_end:
                current_time = now.strftime("%H:%M")
                if not (perm.working_hours_start <= current_time <= perm.working_hours_end):
                    violations.append("outside_working_hours")
                    return False, violations

        return True, violations

    def _matches_scope(
        self,
        perm: ToolPermissionRead,
        department: str | None,
        role: str | None,
    ) -> bool:
        if perm.department and department and perm.department != department:
            return False
        if perm.role and role and perm.role != role:
            return False
        return True
