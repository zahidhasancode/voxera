"""SQLAlchemy conversation turn repository."""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import ConversationTurnModel
from app.memory.repository import ConversationTurnRepository
from app.memory.schemas import AppendMessageRequest, TurnRead


class SqlAlchemyConversationTurnRepository(ConversationTurnRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        turn_index: int,
        data: AppendMessageRequest,
    ) -> TurnRead:
        row = ConversationTurnModel(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            turn_index=turn_index,
            role=data.role.value,
            message=data.message,
            language=data.language or "en",
            latency_ms=data.latency_ms,
            tool_calls=data.tool_calls,
            reasoning_steps=data.reasoning_steps,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return TurnRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TurnRead]:
        result = await self._session.execute(
            select(ConversationTurnModel)
            .where(
                ConversationTurnModel.tenant_id == tenant_id,
                ConversationTurnModel.agent_id == agent_id,
                ConversationTurnModel.conversation_id == conversation_id,
            )
            .order_by(ConversationTurnModel.turn_index)
            .offset(offset)
            .limit(limit)
        )
        return [TurnRead.model_validate(r) for r in result.scalars().all()]

    async def delete_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        result = await self._session.execute(
            delete(ConversationTurnModel).where(
                ConversationTurnModel.tenant_id == tenant_id,
                ConversationTurnModel.agent_id == agent_id,
                ConversationTurnModel.conversation_id == conversation_id,
            )
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def count(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(ConversationTurnModel)
            .where(
                ConversationTurnModel.tenant_id == tenant_id,
                ConversationTurnModel.agent_id == agent_id,
                ConversationTurnModel.conversation_id == conversation_id,
            )
        )
        return int(total or 0)
