"""Verifier agent Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.enums import (
    IdentityVerificationStatus,
    PlannerAction,
    PlannerIntent,
    SessionState,
    VerifierOutcome,
    VerifierRiskLevel,
)
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema
from app.memory.schemas import StructuredSummary
from app.planner.schemas import PlannerPlan
from app.tools.schemas.execution import ToolDefinitionRead


class VerifierInput(SchemaBase):
    """Unified verifier input — planner output + safety context."""

    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    planner_output: PlannerPlan
    conversation_summary: StructuredSummary | None = None
    working_memory: dict[str, str] = Field(default_factory=dict)
    tenant_policies: dict[str, Any] = Field(default_factory=dict)
    allowed_tools: list[ToolDefinitionRead] = Field(default_factory=list)
    current_state: SessionState
    risk_profile: dict[str, Any] = Field(default_factory=dict)
    retrieved_knowledge: list[str] = Field(default_factory=list)
    knowledge_metadata: list[dict[str, Any]] = Field(default_factory=list)
    language: str = "en"
    industry: str | None = None
    identity_status: IdentityVerificationStatus = IdentityVerificationStatus.UNVERIFIED
    planner_decision_id: UUID | None = None


class VerifierResult(SchemaBase):
    """Strict structured verifier output."""

    approved: bool
    outcome: VerifierOutcome
    risk: VerifierRiskLevel
    requires_confirmation: bool = False
    requires_human: bool = False
    reason: str | None = None
    corrected_tool_arguments: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    identity_status: IdentityVerificationStatus | None = None
    compliance_passed: bool = True
    risk_score: float = 0.0
    decision_id: UUID | None = None
    latency_ms: float = 0.0


class VerifyRequest(SchemaBase):
    conversation_id: UUID
    planner_output: PlannerPlan
    planner_decision_id: UUID | None = None
    retrieved_knowledge: list[str] | None = None
    knowledge_metadata: list[dict[str, Any]] | None = None
    tenant_policies: dict[str, Any] | None = None
    risk_profile: dict[str, Any] | None = None
    industry: str | None = None


class ValidationContext(SchemaBase):
    """Internal pipeline context passed between validators."""

    verifier_input: VerifierInput
    violations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    corrected_arguments: dict[str, Any] | None = None
    risk_level: VerifierRiskLevel = VerifierRiskLevel.LOW
    risk_score: float = 0.0
    risk_factors: list[str] = Field(default_factory=list)
    identity_status: IdentityVerificationStatus = IdentityVerificationStatus.UNVERIFIED
    compliance_passed: bool = True
    compliance_findings: list[str] = Field(default_factory=list)
    registered_tool_slugs: set[str] = Field(default_factory=set)
    known_intents: set[str] = Field(default_factory=set)


class VerifierDecisionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID
    planner_decision_id: UUID | None
    approved: bool
    outcome: VerifierOutcome
    risk_level: VerifierRiskLevel
    requires_confirmation: bool
    requires_human: bool
    reason: str | None
    corrected_tool_arguments: dict[str, Any] | None
    warnings: list[str] | None
    violations: list[str] | None
    identity_status: str | None
    latency_ms: float
    token_estimate: int
    provider_name: str = Field(validation_alias="model_provider")


class VerifierHistoryRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID
    decision_id: UUID | None
    status: str
    planner_output: dict[str, Any] | None
    verifier_result: dict[str, Any] | None
    validation_failures: list[str] | None
    policy_violations: list[str] | None
    risk_score: float | None
    identity_status: str | None
    occurred_at: datetime


class VerifierMetricsSnapshot(SchemaBase):
    total_verifications: int = 0
    approval_count: int = 0
    rejection_count: int = 0
    escalation_count: int = 0
    confirmation_required_count: int = 0
    average_latency_ms: float = 0.0
    hallucination_rate: float = 0.0
    policy_rejection_rate: float = 0.0
    approval_rate: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens: int = 0
    risk_distribution: dict[str, int] = Field(default_factory=dict)
