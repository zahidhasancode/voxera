"""SQLAlchemy tool permission repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool_framework import ToolPermissionModel
from app.tools.repository.execution import ToolPermissionRepository
from app.tools.schemas.execution import ToolPermissionRead


class SqlAlchemyToolPermissionRepository(ToolPermissionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        agent_id: UUID | None = None,
    ) -> list[ToolPermissionRead]:
        query = select(ToolPermissionModel).where(ToolPermissionModel.tenant_id == tenant_id)
        if agent_id is not None:
            query = query.where(
                (ToolPermissionModel.agent_id == agent_id) | (ToolPermissionModel.agent_id.is_(None))
            )
        result = await self._session.execute(query)
        return [ToolPermissionRead.model_validate(r) for r in result.scalars().all()]

    async def upsert(self, permission: ToolPermissionRead) -> ToolPermissionRead:
        result = await self._session.execute(
            select(ToolPermissionModel).where(ToolPermissionModel.id == permission.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ToolPermissionModel(
                id=permission.id,
                tenant_id=permission.tenant_id,
                agent_id=permission.agent_id,
                tool_slug=permission.tool_slug,
                effect=permission.effect.value,
                department=permission.department,
                role=permission.role,
                max_executions_per_hour=permission.max_executions_per_hour,
                working_hours_start=permission.working_hours_start,
                working_hours_end=permission.working_hours_end,
                metadata_=None,
            )
            self._session.add(row)
        else:
            row.effect = permission.effect.value
            row.department = permission.department
            row.role = permission.role
            row.max_executions_per_hour = permission.max_executions_per_hour
            row.working_hours_start = permission.working_hours_start
            row.working_hours_end = permission.working_hours_end
        await self._session.flush()
        await self._session.refresh(row)
        return ToolPermissionRead.model_validate(row)
