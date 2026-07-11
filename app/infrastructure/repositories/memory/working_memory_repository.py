"""SQLAlchemy working memory repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import WorkingMemoryModel
from app.memory.repository import WorkingMemoryRepository
from app.memory.schemas import WorkingMemoryRead


class SqlAlchemyWorkingMemoryRepository(WorkingMemoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        key: str,
        value: str,
        *,
        value_type: str = "string",
        language: str | None = None,
        is_sensitive: bool = False,
        expires_at: datetime | None = None,
    ) -> WorkingMemoryRead:
        result = await self._session.execute(
            select(WorkingMemoryModel).where(
                WorkingMemoryModel.tenant_id == tenant_id,
                WorkingMemoryModel.agent_id == agent_id,
                WorkingMemoryModel.conversation_id == conversation_id,
                WorkingMemoryModel.memory_key == key,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = WorkingMemoryModel(
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                memory_key=key,
                value=value,
                value_type=value_type,
                language=language,
                is_sensitive=is_sensitive,
                expires_at=expires_at,
            )
            self._session.add(row)
        else:
            row.value = value
            row.value_type = value_type
            row.language = language
            row.is_sensitive = is_sensitive
            row.expires_at = expires_at
        await self._session.flush()
        await self._session.refresh(row)
        return WorkingMemoryRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> list[WorkingMemoryRead]:
        result = await self._session.execute(
            select(WorkingMemoryModel).where(
                WorkingMemoryModel.tenant_id == tenant_id,
                WorkingMemoryModel.agent_id == agent_id,
                WorkingMemoryModel.conversation_id == conversation_id,
            )
        )
        return [WorkingMemoryRead.model_validate(r) for r in result.scalars().all()]

    async def delete_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        result = await self._session.execute(
            delete(WorkingMemoryModel).where(
                WorkingMemoryModel.tenant_id == tenant_id,
                WorkingMemoryModel.agent_id == agent_id,
                WorkingMemoryModel.conversation_id == conversation_id,
            )
        )
        await self._session.flush()
        return int(result.rowcount or 0)
