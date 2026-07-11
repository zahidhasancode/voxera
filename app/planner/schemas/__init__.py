"""Planner agent Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.enums import (
    PlannerAction,
    PlannerDecisionStatus,
    PlannerIntent,
    PlannerRiskLevel,
    PlannerSessionStatus,
    SessionState,
)
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema
from app.memory.schemas import PlannerContext, StructuredSummary
from app.tools.schemas.execution import ToolDefinitionRead


class ToolCallPlan(SchemaBase):
    tool_slug: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(SchemaBase):
    goal: str
    required_information: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    execution_plan: list[str] = Field(default_factory=list)
    expected_tool: str | None = None
    risk_level: PlannerRiskLevel = PlannerRiskLevel.LOW
    completion_criteria: str = ""


class PlannerPlan(SchemaBase):
    """Strict structured planner output — never free-form text without structure."""

    intent: PlannerIntent
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: list[str] = Field(default_factory=list)
    next_action: str
    action: PlannerAction
    tool_call: ToolCallPlan | None = None
    response: str | None = None
    plan: ExecutionPlan
    status: PlannerDecisionStatus = PlannerDecisionStatus.COMPLETED
    language: str = "en"
    policy_notes: list[str] = Field(default_factory=list)
    retrieval_query: str | None = None


class PlannerInput(SchemaBase):
    """Unified planner input assembled by orchestrator."""

    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    current_user_message: str | None = None
    conversation_summary: StructuredSummary | None = None
    working_memory: dict[str, str] = Field(default_factory=dict)
    retrieved_knowledge: list[str] = Field(default_factory=list)
    available_tools: list[ToolDefinitionRead] = Field(default_factory=list)
    agent_configuration: dict[str, Any] = Field(default_factory=dict)
    tenant_policies: dict[str, Any] = Field(default_factory=dict)
    current_state: SessionState
    planner_history: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    language: str = "en"
    industry: str | None = None

    @classmethod
    def from_context(
        cls,
        context: PlannerContext,
        *,
        available_tools: list[ToolDefinitionRead],
        planner_history: list[dict[str, Any]] | None = None,
        industry: str | None = None,
    ) -> "PlannerInput":
        tool_results = [
            {
                "tool_name": t.tool_name,
                "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                "result": t.result,
                "error": t.error,
            }
            for t in context.tool_results
        ]
        return cls(
            conversation_id=context.conversation_id,
            tenant_id=context.tenant_id,
            agent_id=context.agent_id,
            current_user_message=context.current_user_message,
            conversation_summary=context.conversation_summary,
            working_memory=context.working_memory,
            retrieved_knowledge=context.retrieved_knowledge,
            available_tools=available_tools,
            agent_configuration=context.agent_configuration,
            tenant_policies=context.tenant_policies,
            current_state=context.current_state,
            planner_history=planner_history or [],
            tool_results=tool_results,
            language=context.language,
            industry=industry,
        )


class PlannerHistoryEntry(SchemaBase):
    step_index: int
    intent: PlannerIntent | None = None
    action: PlannerAction | None = None
    reasoning: str | None = None
    occurred_at: datetime | None = None


class PlanRequest(SchemaBase):
    conversation_id: UUID
    user_message: str | None = None
    retrieved_knowledge: list[str] | None = None
    agent_configuration: dict[str, Any] | None = None
    tenant_policies: dict[str, Any] | None = None
    industry: str | None = None
    language: str | None = None


class PlannerDecisionRead(TimestampSchema, TenantScopedSchema):
    model_config = {"protected_namespaces": ()}

    id: UUID
    agent_id: UUID
    conversation_id: UUID
    session_id: UUID
    intent: PlannerIntent
    confidence: float
    action: PlannerAction
    next_action: str | None
    status: PlannerDecisionStatus
    reasoning_steps: list[str] | None
    plan: dict[str, Any] | None
    tool_call: dict[str, Any] | None
    response_text: str | None
    policy_decisions: list[str] | None
    token_estimate: int
    latency_ms: float
    model_provider: str


class PlannerSessionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID
    status: PlannerSessionStatus
    language: str
    reasoning_step_count: int
    last_intent: PlannerIntent | None


class PlannerHistoryRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID
    session_id: UUID
    decision_id: UUID | None
    step_index: int
    intent: PlannerIntent | None
    action: PlannerAction | None
    reasoning: str | None
    occurred_at: datetime


class PlannerMetricsSnapshot(SchemaBase):
    total_plans: int = 0
    success_count: int = 0
    failure_count: int = 0
    escalation_count: int = 0
    average_latency_ms: float = 0.0
    average_confidence: float = 0.0
    average_reasoning_steps: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens: int = 0
    calls_by_intent: dict[str, int] = Field(default_factory=dict)


class OptimizedPlannerContext(SchemaBase):
    """Token-optimized context slice for model planning."""

    current_user_message: str | None
    conversation_summary: StructuredSummary | None
    working_memory: dict[str, str]
    retrieved_knowledge: list[str]
    tool_results: list[dict[str, Any]]
    current_state: SessionState
    language: str
    available_tool_slugs: list[str]
    token_estimate: int = 0
