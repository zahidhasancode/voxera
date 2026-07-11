"""Verifier subsystem factory."""

from functools import lru_cache

from app.infrastructure.memory.factory import build_memory_manager
from app.infrastructure.repositories.verifier.repositories import (
    SqlAlchemyVerifierAuditRepository,
    SqlAlchemyVerifierComplianceRepository,
    SqlAlchemyVerifierDecisionRepository,
    SqlAlchemyVerifierPolicyViolationRepository,
    SqlAlchemyVerifierRiskRepository,
)
from app.infrastructure.tools.factory import build_tool_registry
from app.infrastructure.verifier.verifier_service import VerifierServiceImpl
from app.verifier.audit.audit_service import VerifierAuditService
from app.verifier.cache.base import InMemoryVerifierCache, VerifierCache
from app.verifier.metrics.collector import VerifierMetricsCollector
from app.verifier.models.structured_model import StructuredVerifierModel
from app.verifier.services.verifier_service import VerifierService


@lru_cache
def get_verifier_cache() -> VerifierCache:
    return InMemoryVerifierCache()


@lru_cache
def get_verifier_metrics_collector() -> VerifierMetricsCollector:
    return VerifierMetricsCollector()


def build_verifier_service(session) -> VerifierService:
    audit_repo = SqlAlchemyVerifierAuditRepository(session)
    return VerifierServiceImpl(
        memory_manager=build_memory_manager(session),
        tool_registry=build_tool_registry(session),
        decisions=SqlAlchemyVerifierDecisionRepository(session),
        audit=VerifierAuditService(audit_repo),
        risk_repo=SqlAlchemyVerifierRiskRepository(session),
        policy_repo=SqlAlchemyVerifierPolicyViolationRepository(session),
        compliance_repo=SqlAlchemyVerifierComplianceRepository(session),
        model=StructuredVerifierModel(),
        cache=get_verifier_cache(),
        metrics=get_verifier_metrics_collector(),
    )
