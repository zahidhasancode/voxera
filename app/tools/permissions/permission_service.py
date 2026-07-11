"""Tenant tool permission policy service."""

from uuid import UUID

from app.tools.repository.execution import ToolPermissionRepository
from app.tools.schemas.execution import ToolPermissionRead
from app.tools.validators.access_validator import ToolPermissionEvaluator


class ToolPermissionService:
    """Evaluates and manages tenant tool permissions."""

    def __init__(
        self,
        repository: ToolPermissionRepository,
        evaluator: ToolPermissionEvaluator | None = None,
    ) -> None:
        self._repository = repository
        self._evaluator = evaluator or ToolPermissionEvaluator()

    async def list_permissions(
        self,
        tenant_id: UUID,
        *,
        agent_id: UUID | None = None,
    ) -> list[ToolPermissionRead]:
        return await self._repository.list_for_tenant(tenant_id, agent_id=agent_id)

    async def is_allowed(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
        *,
        department: str | None = None,
        role: str | None = None,
        executions_last_hour: int = 0,
    ) -> tuple[bool, list[str]]:
        perms = await self._repository.list_for_tenant(tenant_id, agent_id=agent_id)
        return self._evaluator.evaluate(
            tool_slug=tool_slug,
            permissions=perms,
            department=department,
            role=role,
            executions_last_hour=executions_last_hour,
        )
