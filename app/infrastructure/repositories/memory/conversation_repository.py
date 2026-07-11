"""SQLAlchemy conversation repository."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import ConversationStatus, SessionState
from app.database.models.memory import ConversationModel
from app.memory.repository import ConversationRepository
from app.memory.schemas import CreateSessionRequest, SessionRead


class SqlAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CreateSessionRequest, *, expires_at: datetime | None) -> SessionRead:
        now = datetime.now(timezone.utc)
        if expires_at is None:
            expires_at = now + timedelta(hours=settings.MEMORY_SESSION_EXPIRY_HOURS)
        row = ConversationModel(
            tenant_id=data.tenant_id,
            agent_id=data.agent_id,
            language=data.language,
            metadata_=data.metadata,
            started_at=now,
            expires_at=expires_at,
            status=ConversationStatus.ACTIVE,
            current_state=SessionState.CALL_STARTED,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def get(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        return SessionRead.model_validate(row) if row else None

    async def update_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        state: SessionState,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        if row is None:
            return None
        row.current_state = state.value
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def update_language(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        language: str,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        if row is None:
            return None
        row.language = language
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def increment_turn_count(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> None:
        await self._session.execute(
            update(ConversationModel)
            .where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.agent_id == agent_id,
                ConversationModel.id == conversation_id,
            )
            .values(turn_count=ConversationModel.turn_count + 1)
        )
        await self._session.flush()

    async def mark_completed(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        if row is None:
            return None
        row.status = ConversationStatus.COMPLETED
        row.current_state = SessionState.CALL_COMPLETED
        row.ended_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def mark_archived(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        if row is None:
            return None
        row.status = ConversationStatus.ARCHIVED
        row.ended_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def mark_expired(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead | None:
        row = await self._get_row(tenant_id, agent_id, conversation_id)
        if row is None:
            return None
        row.status = ConversationStatus.EXPIRED
        await self._session.flush()
        await self._session.refresh(row)
        return SessionRead.model_validate(row)

    async def _get_row(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> ConversationModel | None:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.tenant_id == tenant_id,
                ConversationModel.agent_id == agent_id,
                ConversationModel.id == conversation_id,
            )
        )
        return result.scalar_one_or_none()
