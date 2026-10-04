"""VerifierService implementation."""

import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import IdentityVerificationStatus, WorkingMemoryKey
from app.infrastructure.repositories.verifier.repositories import (
    SqlAlchemyVerifierComplianceRepository,
    SqlAlchemyVerifierDecisionRepository,
    SqlAlchemyVerifierPolicyViolationRepository,
    SqlAlchemyVerifierRiskRepository,
)
from app.memory.manager.memory_manager import MemoryManager
from app.tools.registry.tool_registry import ToolRegistry
from app.verifier.audit.audit_service import VerifierAuditService
from app.verifier.cache.base import VerifierCache
from app.verifier.metrics.collector import VerifierMetricsCollector
from app.verifier.models.structured_model import StructuredVerifierModel
from app.verifier.schemas import (
    VerifyRequest,
    VerifierDecisionRead,
    VerifierHistoryRead,
    VerifierInput,
    VerifierMetricsSnapshot,
    VerifierResult,
)
from app.verifier.services.verifier_service import VerifierService
from app.verifier.validators.access_validator import VerifierAccessValidator


class VerifierServiceImpl(VerifierService):
    """Enterprise verifier — validates every planner decision before execution."""

    def __init__(
        self,
        *,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
        decisions: SqlAlchemyVerifierDecisionRepository,
        audit: VerifierAuditService,
        risk_repo: SqlAlchemyVerifierRiskRepository,
        policy_repo: SqlAlchemyVerifierPolicyViolationRepository,
        compliance_repo: SqlAlchemyVerifierComplianceRepository,
        model: StructuredVerifierModel | None = None,
        access_validator: VerifierAccessValidator | None = None,
        cache: VerifierCache | None = None,
        metrics: VerifierMetricsCollector | None = None,
    ) -> None:
        self._memory = memory_manager
        self._tools = tool_registry
        self._decisions = decisions
        self._audit = audit
        self._risk_repo = risk_repo
        self._policy_repo = policy_repo
        self._compliance_repo = compliance_repo
        self._model = model or StructuredVerifierModel()
        self._access = access_validator or VerifierAccessValidator()
        self._cache = cache
        self._metrics = metrics or VerifierMetricsCollector()

    async def verify(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        request: VerifyRequest,
    ) -> VerifierResult:
        start = time.perf_counter()
        cache_key = f"verify:{tenant_id}:{agent_id}:{request.conversation_id}:{hash(str(request.planner_output.model_dump()))}"

        if self._cache and settings.VERIFIER_ENABLE_CACHE:
            cached = await self._cache.get(cache_key)
            if cached:
                self._metrics.cache_hits += 1
                return VerifierResult.model_validate(cached)
            self._metrics.cache_misses += 1

        memory_context = await self._memory.get_context(
            tenant_id,
            agent_id,
            request.conversation_id,
            retrieved_knowledge=request.retrieved_knowledge,
            tenant_policies=request.tenant_policies,
        )
        self._access.validate_scope(
            tenant_id=tenant_id,
            agent_id=agent_id,
            resource_tenant_id=memory_context.tenant_id,
            resource_agent_id=memory_context.agent_id,
        )

        allowed_tools = await self._tools.list_tools(tenant_id, agent_id)
        wm = dict(memory_context.working_memory)

        identity_status = IdentityVerificationStatus.UNVERIFIED
        ver = wm.get(WorkingMemoryKey.VERIFICATION_STATUS, wm.get("verification_status", "")).lower()
        if ver == "verified":
            identity_status = IdentityVerificationStatus.VERIFIED
        elif ver == "pending":
            identity_status = IdentityVerificationStatus.PENDING

        verifier_input = VerifierInput(
            conversation_id=request.conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            planner_output=request.planner_output,
            conversation_summary=memory_context.conversation_summary,
            working_memory=wm,
            tenant_policies=request.tenant_policies or memory_context.tenant_policies,
            allowed_tools=allowed_tools,
            current_state=memory_context.current_state,
            risk_profile=request.risk_profile or {},
            retrieved_knowledge=request.retrieved_knowledge or memory_context.retrieved_knowledge,
            knowledge_metadata=request.knowledge_metadata or [],
            language=memory_context.language,
            industry=request.industry,
            identity_status=identity_status,
            planner_decision_id=request.planner_decision_id,
        )

        result = await self._model.verify(verifier_input)
        elapsed_ms = (time.perf_counter() - start) * 1000
        tokens = self._model.estimate_tokens(verifier_input)

        decision_id = uuid4()
        now = datetime.now(timezone.utc)
        policy_violations = [v for v in result.violations if "blocked" in v or "not_allowed" in v or "policy" in v]

        decision = VerifierDecisionRead(
            id=decision_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            planner_decision_id=request.planner_decision_id,
            approved=result.approved,
            outcome=result.outcome,
            risk_level=result.risk,
            requires_confirmation=result.requires_confirmation,
            requires_human=result.requires_human,
            reason=result.reason,
            corrected_tool_arguments=result.corrected_tool_arguments,
            warnings=result.warnings,
            violations=result.violations,
            identity_status=result.identity_status.value if result.identity_status else None,
            latency_ms=elapsed_ms,
            token_estimate=tokens,
            provider_name=self._model.provider_name,
            created_at=now,
            updated_at=now,
        )
        await self._decisions.create(decision)

        await self._risk_repo.record_assessment(
            {
                "id": uuid4(),
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "conversation_id": request.conversation_id,
                "decision_id": decision_id,
                "risk_level": result.risk.value,
                "intent": request.planner_output.intent.value,
                "tool_slug": request.planner_output.tool_call.tool_slug if request.planner_output.tool_call else None,
                "action": request.planner_output.action.value,
                "factors": result.warnings,
                "score": result.risk_score,
            }
        )

        if policy_violations:
            await self._policy_repo.record_violations(
                decision_id,
                [
                    {
                        "id": uuid4(),
                        "tenant_id": tenant_id,
                        "agent_id": agent_id,
                        "conversation_id": request.conversation_id,
                        "policy_key": v.split(":")[0] if ":" in v else "general",
                        "violation_type": "policy",
                        "message": v,
                        "severity": "high",
                    }
                    for v in policy_violations
                ],
            )

        if not result.compliance_passed:
            await self._compliance_repo.record_checks(
                decision_id,
                [
                    {
                        "id": uuid4(),
                        "tenant_id": tenant_id,
                        "agent_id": agent_id,
                        "conversation_id": request.conversation_id,
                        "framework": "compliance",
                        "passed": False,
                        "findings": result.violations,
                        "checked_at": now,
                    }
                ],
            )

        await self._audit.log_verification(
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            decision_id=decision_id,
            verifier_input=verifier_input,
            result=result,
            validation_failures=result.violations,
            policy_violations=policy_violations,
        )

        result.decision_id = decision_id
        result.latency_ms = elapsed_ms

        self._metrics.record(
            approved=result.approved,
            outcome=result.outcome.value,
            latency_ms=elapsed_ms,
            tokens=tokens,
            violations=result.violations,
            risk=result.risk.value,
        )

        if self._cache and settings.VERIFIER_ENABLE_CACHE:
            await self._cache.set(cache_key, result.model_dump(mode="json"), ttl_seconds=settings.VERIFIER_CACHE_TTL_SECONDS)

        return result

    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 50,
    ) -> list[VerifierHistoryRead]:
        return await self._audit.list_history(
            tenant_id, agent_id, conversation_id, limit=limit
        )

    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        *,
        conversation_id: UUID | None = None,
    ) -> VerifierMetricsSnapshot:
        db = await self._decisions.metrics_snapshot(tenant_id, agent_id, conversation_id=conversation_id)
        snap = self._metrics.snapshot()
        if not db:
            return snap
        return VerifierMetricsSnapshot(
            total_verifications=db.get("total_verifications", 0) + snap.total_verifications,
            approval_count=db.get("approval_count", 0) + snap.approval_count,
            rejection_count=db.get("rejection_count", 0) + snap.rejection_count,
            escalation_count=db.get("escalation_count", 0) + snap.escalation_count,
            confirmation_required_count=db.get("confirmation_required_count", 0) + snap.confirmation_required_count,
            average_latency_ms=db.get("average_latency_ms", snap.average_latency_ms),
            hallucination_rate=snap.hallucination_rate,
            policy_rejection_rate=snap.policy_rejection_rate,
            approval_rate=(db.get("approval_count", 0) + snap.approval_count) / max(db.get("total_verifications", 0) + snap.total_verifications, 1),
            cache_hits=snap.cache_hits,
            cache_misses=snap.cache_misses,
            total_tokens=snap.total_tokens,
            risk_distribution={**db.get("risk_distribution", {}), **snap.risk_distribution},
        )
