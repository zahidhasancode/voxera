"""SQLAlchemy conversation summary repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import ConversationSummaryModel
from app.memory.repository import ConversationSummaryRepository
from app.memory.schemas import StructuredSummary, SummaryRead


class SqlAlchemyConversationSummaryRepository(ConversationSummaryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        summary: StructuredSummary,
        *,
        turn_count: int,
    ) -> SummaryRead:
        row = ConversationSummaryModel(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            customer_identity=summary.customer_identity,
            conversation_goal=summary.conversation_goal,
            resolved_items=summary.resolved_items,
            pending_items=summary.pending_items,
            collected_information=summary.collected_information,
            summary_text=summary.summary_text,
            token_estimate=summary.token_estimate,
            turn_count_at_summary=turn_count,
            language=summary.language,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return SummaryRead.model_validate(row)

    async def get_latest(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SummaryRead | None:
        result = await self._session.execute(
            select(ConversationSummaryModel)
            .where(
                ConversationSummaryModel.tenant_id == tenant_id,
                ConversationSummaryModel.agent_id == agent_id,
                ConversationSummaryModel.conversation_id == conversation_id,
            )
            .order_by(ConversationSummaryModel.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return SummaryRead.model_validate(row) if row else None
