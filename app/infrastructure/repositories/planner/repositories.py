"""SQLAlchemy planner repositories."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PlannerSessionStatus
from app.database.models.planner import (
    PlannerDecisionModel,
    PlannerHistoryModel,
    PlannerSessionModel,
)
from app.planner.repository import (
    PlannerDecisionRepository,
    PlannerHistoryRepository,
    PlannerMetricsRepository,
    PlannerSessionRepository,
)
from app.planner.schemas import PlannerDecisionRead, PlannerHistoryRead, PlannerSessionRead


class SqlAlchemyPlannerSessionRepository(PlannerSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        language: str = "en",
    ) -> PlannerSessionRead:
        result = await self._session.execute(
            select(PlannerSessionModel).where(
                PlannerSessionModel.tenant_id == tenant_id,
                PlannerSessionModel.agent_id == agent_id,
                PlannerSessionModel.conversation_id == conversation_id,
                PlannerSessionModel.status == PlannerSessionStatus.ACTIVE,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = PlannerSessionModel(
                tenant_id=tenant_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                status=PlannerSessionStatus.ACTIVE,
                language=language,
            )
            self._session.add(row)
            await self._session.flush()
            await self._session.refresh(row)
        return PlannerSessionRead.model_validate(row)

    async def increment_steps(self, session_id: UUID, *, intent: str | None = None) -> PlannerSessionRead:
        result = await self._session.execute(
            select(PlannerSessionModel).where(PlannerSessionModel.id == session_id)
        )
        row = result.scalar_one()
        row.reasoning_step_count += 1
        if intent:
            row.last_intent = intent
        await self._session.flush()
        await self._session.refresh(row)
        return PlannerSessionRead.model_validate(row)


class SqlAlchemyPlannerDecisionRepository(PlannerDecisionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, decision: PlannerDecisionRead) -> PlannerDecisionRead:
        row = PlannerDecisionModel(
            id=decision.id,
            tenant_id=decision.tenant_id,
            agent_id=decision.agent_id,
            conversation_id=decision.conversation_id,
            session_id=decision.session_id,
            intent=decision.intent.value,
            confidence=decision.confidence,
            action=decision.action.value,
            next_action=decision.next_action,
            status=decision.status.value,
            reasoning_steps=decision.reasoning_steps,
            plan=decision.plan,
            tool_call=decision.tool_call,
            response_text=decision.response_text,
            policy_decisions=decision.policy_decisions,
            token_estimate=decision.token_estimate,
            latency_ms=decision.latency_ms,
            model_provider=decision.model_provider,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return PlannerDecisionRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[PlannerDecisionRead]:
        result = await self._session.execute(
            select(PlannerDecisionModel)
            .where(
                PlannerDecisionModel.tenant_id == tenant_id,
                PlannerDecisionModel.agent_id == agent_id,
                PlannerDecisionModel.conversation_id == conversation_id,
            )
            .order_by(PlannerDecisionModel.created_at.desc())
            .limit(limit)
        )
        return [PlannerDecisionRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyPlannerHistoryRepository(PlannerHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, entry: PlannerHistoryRead) -> PlannerHistoryRead:
        row = PlannerHistoryModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            agent_id=entry.agent_id,
            conversation_id=entry.conversation_id,
            session_id=entry.session_id,
            decision_id=entry.decision_id,
            step_index=entry.step_index,
            intent=entry.intent.value if entry.intent else None,
            action=entry.action.value if entry.action else None,
            reasoning=entry.reasoning,
            occurred_at=entry.occurred_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return PlannerHistoryRead.model_validate(row)

    async def list_by_conversation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[PlannerHistoryRead]:
        result = await self._session.execute(
            select(PlannerHistoryModel)
            .where(
                PlannerHistoryModel.tenant_id == tenant_id,
                PlannerHistoryModel.agent_id == agent_id,
                PlannerHistoryModel.conversation_id == conversation_id,
            )
            .order_by(PlannerHistoryModel.occurred_at.desc())
            .limit(limit)
        )
        return [PlannerHistoryRead.model_validate(r) for r in result.scalars().all()]


class SqlAlchemyPlannerMetricsRepository(PlannerMetricsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def snapshot(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> dict:
        query = select(PlannerDecisionModel).where(
            PlannerDecisionModel.tenant_id == tenant_id,
            PlannerDecisionModel.agent_id == agent_id,
        )
        if conversation_id:
            query = query.where(PlannerDecisionModel.conversation_id == conversation_id)
        result = await self._session.execute(query)
        rows = list(result.scalars().all())
        if not rows:
            return {}
        intents: dict[str, int] = {}
        for r in rows:
            intents[r.intent] = intents.get(r.intent, 0) + 1
        return {
            "total_plans": len(rows),
            "success_count": sum(1 for r in rows if r.status == "completed"),
            "failure_count": sum(1 for r in rows if r.status == "failed"),
            "escalation_count": sum(1 for r in rows if r.status == "escalated"),
            "average_latency_ms": sum(r.latency_ms for r in rows) / len(rows),
            "average_confidence": sum(r.confidence for r in rows) / len(rows),
            "average_reasoning_steps": sum(len(r.reasoning_steps or []) for r in rows) / len(rows),
            "cache_hits": 0,
            "cache_misses": 0,
            "total_tokens": sum(r.token_estimate for r in rows),
            "calls_by_intent": intents,
        }
