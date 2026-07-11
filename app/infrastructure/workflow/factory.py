"""Workflow subsystem factory."""

from functools import lru_cache

from app.infrastructure.repositories.workflow.repositories import (
    SqlAlchemyBusinessPolicyRepository,
    SqlAlchemyRoutingRuleRepository,
    SqlAlchemyWorkflowAuditRepository,
    SqlAlchemyWorkflowExecutionRepository,
    SqlAlchemyWorkflowRepository,
    SqlAlchemyWorkflowRuleRepository,
)
from app.infrastructure.workflow.workflow_engine_impl import WorkflowEngineImpl
from app.workflow.audit.audit_service import WorkflowAuditService
from app.workflow.engine.event_bus import WorkflowEventBus
from app.workflow.metrics.collector import WorkflowMetricsCollector
from app.workflow.services.workflow_service import WorkflowService


@lru_cache
def get_workflow_event_bus() -> WorkflowEventBus:
    return WorkflowEventBus()


@lru_cache
def get_workflow_metrics_collector() -> WorkflowMetricsCollector:
    return WorkflowMetricsCollector()


def build_workflow_service(session) -> WorkflowService:
    workflows = SqlAlchemyWorkflowRepository(session)
    audit_repo = SqlAlchemyWorkflowAuditRepository(session)
    engine = WorkflowEngineImpl(
        workflows=workflows,
        executions=SqlAlchemyWorkflowExecutionRepository(session),
        rules_repo=SqlAlchemyWorkflowRuleRepository(session),
        policies_repo=SqlAlchemyBusinessPolicyRepository(session),
        routing_repo=SqlAlchemyRoutingRuleRepository(session),
        audit=WorkflowAuditService(audit_repo),
        event_bus=get_workflow_event_bus(),
        metrics=get_workflow_metrics_collector(),
    )
    return WorkflowService(engine, workflows)
