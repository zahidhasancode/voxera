"""PlannerService implementation."""

import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import PlannerAction, PlannerDecisionStatus
from app.core.exceptions import PlannerConfidenceTooLowError, PlannerPolicyViolationError
from app.memory.manager.memory_manager import MemoryManager
from app.planner.cache.base import PlannerCache
from app.planner.metrics.collector import PlannerMetricsCollector
from app.planner.models.structured_model import StructuredPlannerModel
from app.planner.policies.policy_engine import PolicyEngine
from app.planner.repository import (
    PlannerDecisionRepository,
    PlannerHistoryRepository,
    PlannerMetricsRepository,
    PlannerSessionRepository,
)
from app.planner.schemas import (
    PlanRequest,
    PlannerDecisionRead,
    PlannerHistoryRead,
    PlannerInput,
    PlannerPlan,
    PlannerMetricsSnapshot,
)
from app.planner.services.planner_service import PlannerService
from app.planner.state.context_optimizer import ContextOptimizer
from app.planner.validators.access_validator import PlannerAccessValidator
from app.planner.validators.output_validator import PlannerOutputValidator
from app.tools.registry.tool_registry import ToolRegistry


class PlannerServiceImpl(PlannerService):
    """Enterprise planner orchestrator — plans only, never executes."""

    def __init__(
        self,
        *,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
        sessions: PlannerSessionRepository,
        decisions: PlannerDecisionRepository,
        history: PlannerHistoryRepository,
        metrics_repo: PlannerMetricsRepository,
        model: StructuredPlannerModel | None = None,
        policy_engine: PolicyEngine | None = None,
        context_optimizer: ContextOptimizer | None = None,
        output_validator: PlannerOutputValidator | None = None,
        access_validator: PlannerAccessValidator | None = None,
        cache: PlannerCache | None = None,
        metrics: PlannerMetricsCollector | None = None,
    ) -> None:
        self._memory = memory_manager
        self._tools = tool_registry
        self._sessions = sessions
        self._decisions = decisions
        self._history = history
        self._metrics_repo = metrics_repo
        self._model = model or StructuredPlannerModel()
        self._policy = policy_engine or PolicyEngine()
        self._optimizer = context_optimizer or ContextOptimizer()
        self._validator = output_validator or PlannerOutputValidator()
        self._access = access_validator or PlannerAccessValidator()
        self._cache = cache
        self._metrics = metrics or PlannerMetricsCollector()

    async def plan(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: PlanRequest,
    ) -> PlannerPlan:
        start = time.perf_counter()
        cache_key = self._cache_key(tenant_id, agent_id, request)

        if self._cache and settings.PLANNER_ENABLE_CACHE:
            cached = await self._cache.get(cache_key)
            if cached:
                self._metrics.record_cache_hit()
                return PlannerPlan.model_validate(cached)
            self._metrics.record_cache_miss()

        memory_context = await self._memory.get_context(
            tenant_id,
            agent_id,
            request.conversation_id,
            retrieved_knowledge=request.retrieved_knowledge,
            agent_configuration=request.agent_configuration,
            tenant_policies=request.tenant_policies,
        )
        self._access.validate_scope(
            tenant_id=tenant_id,
            agent_id=agent_id,
            resource_tenant_id=memory_context.tenant_id,
            resource_agent_id=memory_context.agent_id,
        )

        if request.user_message:
            memory_context = memory_context.model_copy(update={"current_user_message": request.user_message})

        available_tools = await self._tools.list_tools(tenant_id, agent_id)
        history_rows = await self._history.list_by_conversation(
            tenant_id, agent_id, request.conversation_id, limit=10
        )
        planner_history = [
            {
                "step_index": h.step_index,
                "intent": h.intent,
                "action": h.action,
                "reasoning": h.reasoning,
                "occurred_at": h.occurred_at,
            }
            for h in history_rows
        ]

        planner_input = PlannerInput.from_context(
            memory_context,
            available_tools=available_tools,
            planner_history=planner_history,
            industry=request.industry,
        )
        if request.language:
            planner_input = planner_input.model_copy(update={"language": request.language})

        optimized = self._optimizer.optimize(planner_input)

        try:
            plan = await self._model.plan(optimized, planner_input)
            plan, policy_notes = self._policy.evaluate(planner_input, plan)
            plan.policy_notes = policy_notes
        except PlannerPolicyViolationError:
            raise
        except Exception as exc:
            plan = self._recovery_plan(planner_input, str(exc))

        if plan.confidence < settings.PLANNER_MIN_CONFIDENCE and plan.action not in (
            PlannerAction.ASK_CLARIFICATION,
            PlannerAction.TRANSFER_HUMAN,
        ):
            raise PlannerConfidenceTooLowError(
                f"Confidence {plan.confidence:.2f} below threshold {settings.PLANNER_MIN_CONFIDENCE}",
                confidence=plan.confidence,
            )

        self._validator.validate(plan)

        session = await self._sessions.get_or_create(
            tenant_id,
            agent_id,
            request.conversation_id,
            language=planner_input.language,
        )
        await self._sessions.increment_steps(session.id, intent=plan.intent.value)

        elapsed_ms = (time.perf_counter() - start) * 1000
        tokens = self._model.estimate_tokens(optimized)
        decision_id = uuid4()
        now = datetime.now(timezone.utc)

        decision = PlannerDecisionRead(
            id=decision_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            session_id=session.id,
            intent=plan.intent,
            confidence=plan.confidence,
            action=plan.action,
            next_action=plan.next_action,
            status=plan.status,
            reasoning_steps=plan.reasoning,
            plan=plan.plan.model_dump(mode="json"),
            tool_call=plan.tool_call.model_dump(mode="json") if plan.tool_call else None,
            response_text=plan.response,
            policy_decisions=plan.policy_notes,
            token_estimate=tokens,
            latency_ms=elapsed_ms,
            model_provider=self._model.provider_name,
            created_at=now,
            updated_at=now,
        )
        await self._decisions.create(decision)

        for idx, step in enumerate(plan.reasoning):
            await self._history.append(
                PlannerHistoryRead(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    conversation_id=request.conversation_id,
                    session_id=session.id,
                    decision_id=decision_id,
                    step_index=idx,
                    intent=plan.intent if idx == 0 else None,
                    action=plan.action if idx == len(plan.reasoning) - 1 else None,
                    reasoning=step,
                    occurred_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )

        self._metrics.record_plan(
            intent=plan.intent.value,
            success=plan.status != PlannerDecisionStatus.FAILED,
            latency_ms=elapsed_ms,
            confidence=plan.confidence,
            reasoning_steps=len(plan.reasoning),
            tokens=tokens,
            escalated=plan.status == PlannerDecisionStatus.ESCALATED,
        )

        if self._cache and settings.PLANNER_ENABLE_CACHE:
            await self._cache.set(cache_key, plan.model_dump(mode="json"), ttl_seconds=settings.PLANNER_CACHE_TTL_SECONDS)

        return plan

    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[PlannerHistoryRead]:
        return await self._history.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=limit
        )

    async def get_decisions(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 20,
    ) -> list[PlannerDecisionRead]:
        return await self._decisions.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=limit
        )

    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> PlannerMetricsSnapshot:
        db = await self._metrics_repo.snapshot(tenant_id, agent_id, conversation_id=conversation_id)
        return self._metrics.merge_db(db)

    def _cache_key(self, tenant_id: UUID, agent_id: UUID, request: PlanRequest) -> str:
        msg = request.user_message or ""
        return f"planner:{tenant_id}:{agent_id}:{request.conversation_id}:{hash(msg)}"

    def _recovery_plan(self, planner_input: PlannerInput, error: str) -> PlannerPlan:
        from app.core.enums import PlannerIntent, PlannerRiskLevel
        from app.planner.schemas import ExecutionPlan

        return PlannerPlan(
            intent=PlannerIntent.UNKNOWN,
            confidence=0.50,
            reasoning=[f"Planner recovery triggered: {error}", "Defaulting to clarification"],
            next_action="clarify_intent",
            action=PlannerAction.ASK_CLARIFICATION,
            response="I want to make sure I understand correctly. Could you rephrase your request?",
            plan=ExecutionPlan(
                goal="Recover from planning failure",
                required_information=["clarification"],
                missing_information=["clear_intent"],
                execution_plan=["Ask customer to clarify"],
                risk_level=PlannerRiskLevel.LOW,
                completion_criteria="Intent clarified",
            ),
            status=PlannerDecisionStatus.FAILED,
            language=planner_input.language,
            policy_notes=["recovery_mode"],
        )
