"""SQLAlchemy tool framework execution repository."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ToolFrameworkExecutionStatus
from app.database.models.tool_framework import ToolFrameworkExecutionModel
from app.tools.repository.execution import ToolFrameworkExecutionRepository
from app.tools.schemas.execution import ToolExecutionRead


class SqlAlchemyToolFrameworkExecutionRepository(ToolFrameworkExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, execution: ToolExecutionRead) -> ToolExecutionRead:
        row = ToolFrameworkExecutionModel(
            id=execution.id,
            tenant_id=execution.tenant_id,
            agent_id=execution.agent_id,
            conversation_id=execution.conversation_id,
            tool_slug=execution.tool_slug,
            tool_name=execution.tool_name,
            status=execution.status.value,
            arguments=execution.arguments,
            result=execution.result,
            error=execution.error,
            execution_time_ms=execution.execution_time_ms,
            retry_count=execution.retry_count,
            idempotency_key=execution.idempotency_key,
            metadata_=None,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ToolExecutionRead.model_validate(row)

    async def get_by_idempotency(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        idempotency_key: str,
    ) -> ToolExecutionRead | None:
        result = await self._session.execute(
            select(ToolFrameworkExecutionModel).where(
                ToolFrameworkExecutionModel.tenant_id == tenant_id,
                ToolFrameworkExecutionModel.agent_id == agent_id,
                ToolFrameworkExecutionModel.idempotency_key == idempotency_key,
            )
        )
        row = result.scalar_one_or_none()
        return ToolExecutionRead.model_validate(row) if row else None

    async def list_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
        tool_slug: str | None = None,
        limit: int = 50,
    ) -> list[ToolExecutionRead]:
        query = select(ToolFrameworkExecutionModel).where(
            ToolFrameworkExecutionModel.tenant_id == tenant_id,
            ToolFrameworkExecutionModel.agent_id == agent_id,
        )
        if conversation_id is not None:
            query = query.where(ToolFrameworkExecutionModel.conversation_id == conversation_id)
        if tool_slug is not None:
            query = query.where(ToolFrameworkExecutionModel.tool_slug == tool_slug)
        query = query.order_by(ToolFrameworkExecutionModel.created_at.desc()).limit(limit)
        result = await self._session.execute(query)
        return [ToolExecutionRead.model_validate(r) for r in result.scalars().all()]

    async def count_since(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        tool_slug: str,
        *,
        since_minutes: int = 60,
    ) -> int:
        since = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        result = await self._session.execute(
            select(func.count())
            .select_from(ToolFrameworkExecutionModel)
            .where(
                ToolFrameworkExecutionModel.tenant_id == tenant_id,
                ToolFrameworkExecutionModel.agent_id == agent_id,
                ToolFrameworkExecutionModel.tool_slug == tool_slug,
                ToolFrameworkExecutionModel.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def metrics_snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        tool_slug: str | None = None,
    ) -> dict:
        query = select(ToolFrameworkExecutionModel).where(
            ToolFrameworkExecutionModel.tenant_id == tenant_id,
            ToolFrameworkExecutionModel.agent_id == agent_id,
        )
        if tool_slug:
            query = query.where(ToolFrameworkExecutionModel.tool_slug == tool_slug)
        result = await self._session.execute(query)
        rows = list(result.scalars().all())
        if not rows:
            return {
                "total_executions": 0,
                "success_count": 0,
                "failure_count": 0,
                "permission_denied_count": 0,
                "validation_failure_count": 0,
                "average_latency_ms": 0.0,
                "calls_by_tool": {},
            }
        success = sum(1 for r in rows if r.status == ToolFrameworkExecutionStatus.SUCCESS)
        failures = sum(
            1
            for r in rows
            if r.status
            in (
                ToolFrameworkExecutionStatus.FAILED,
                ToolFrameworkExecutionStatus.TIMEOUT,
                ToolFrameworkExecutionStatus.CIRCUIT_OPEN,
            )
        )
        perm_denied = sum(1 for r in rows if r.status == ToolFrameworkExecutionStatus.PERMISSION_DENIED)
        validation = sum(1 for r in rows if r.status == ToolFrameworkExecutionStatus.VALIDATION_FAILED)
        avg_latency = sum(r.execution_time_ms for r in rows) / len(rows)
        calls: dict[str, int] = {}
        for r in rows:
            calls[r.tool_slug] = calls.get(r.tool_slug, 0) + 1
        return {
            "total_executions": len(rows),
            "success_count": success,
            "failure_count": failures,
            "permission_denied_count": perm_denied,
            "validation_failure_count": validation,
            "average_latency_ms": avg_latency,
            "calls_by_tool": calls,
        }
