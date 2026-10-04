"""Workflow engine Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.enums import (
    RoutingStrategy,
    RuleActionType,
    RuleOperator,
    WorkflowEventType,
    WorkflowExecutionStatus,
    WorkflowState,
)
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class RuleCondition(SchemaBase):
    field: str
    operator: RuleOperator
    value: Any


class RuleAction(SchemaBase):
    type: RuleActionType
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowRuleDefinition(SchemaBase):
    name: str
    priority: int = 100
    enabled: bool = True
    conditions: list[RuleCondition]
    actions: list[RuleAction]
    else_actions: list[RuleAction] = Field(default_factory=list)


class BusinessPolicyConfig(SchemaBase):
    working_hours_start: str | None = None
    working_hours_end: str | None = None
    timezone: str = "UTC"
    holidays: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    departments: list[str] = Field(default_factory=list)
    max_refund: float | None = None
    max_discount: float | None = None
    escalation_threshold: float | None = None
    vip_rules: dict[str, Any] = Field(default_factory=dict)
    compliance_frameworks: list[str] = Field(default_factory=list)
    allowed_tools: list[str] | None = None
    blocked_tools: list[str] | None = None
    max_autonomy: str = "full"


class RoutingRuleDefinition(SchemaBase):
    name: str
    strategy: RoutingStrategy
    priority: int = 100
    enabled: bool = True
    conditions: list[RuleCondition]
    target: dict[str, Any]


class WorkflowDefinition(SchemaBase):
    slug: str
    name: str
    description: str | None = None
    version: str = "1.0.0"
    enabled: bool = True
    steps: list[dict[str, Any]] = Field(default_factory=list)
    rules: list[WorkflowRuleDefinition] = Field(default_factory=list)
    approval_chain: list[dict[str, Any]] = Field(default_factory=list)
    escalation_policy: dict[str, Any] = Field(default_factory=dict)
    routing_rules: list[RoutingRuleDefinition] = Field(default_factory=list)


class WorkflowRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    slug: str
    name: str
    description: str | None
    version: str
    enabled: bool
    definition: dict[str, Any]


class WorkflowCreate(SchemaBase):
    slug: str = Field(..., min_length=2, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    version: str = "1.0.0"
    enabled: bool = True
    definition: dict[str, Any]


class WorkflowExecutionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    workflow_id: UUID
    conversation_id: UUID
    status: WorkflowExecutionStatus
    current_state: WorkflowState
    context: dict[str, Any] | None
    step_index: int
    retry_count: int
    started_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime | None
    error: str | None


class WorkflowStepResult(SchemaBase):
    state: WorkflowState
    status: WorkflowExecutionStatus
    actions_taken: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    approval_id: UUID | None = None
    escalation_id: UUID | None = None
    routing_target: dict[str, Any] | None = None
    policy_violations: list[str] = Field(default_factory=list)
    events: list[WorkflowEventType] = Field(default_factory=list)
    completed: bool = False
    message: str | None = None


class StartWorkflowRequest(SchemaBase):
    conversation_id: UUID
    workflow_slug: str | None = None
    workflow_id: UUID | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    planner_output: dict[str, Any] | None = None
    verifier_result: dict[str, Any] | None = None


class AdvanceWorkflowRequest(SchemaBase):
    execution_id: UUID
    event: str | None = None
    context_updates: dict[str, Any] = Field(default_factory=dict)


class ApproveWorkflowRequest(SchemaBase):
    execution_id: UUID
    approval_id: UUID
    approver_id: str | None = None
    approved: bool = True
    reason: str | None = None


class TestWorkflowRequest(SchemaBase):
    workflow_slug: str | None = None
    definition: dict[str, Any] | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ValidateWorkflowRequest(SchemaBase):
    definition: dict[str, Any]


class WorkflowEvent(SchemaBase):
    event_type: WorkflowEventType
    execution_id: UUID | None = None
    tenant_id: UUID
    agent_id: UUID
    conversation_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class WorkflowMetricsSnapshot(SchemaBase):
    total_executions: int = 0
    completed_count: int = 0
    failed_count: int = 0
    escalated_count: int = 0
    average_duration_ms: float = 0.0
    average_approval_time_ms: float = 0.0
    escalation_rate: float = 0.0
    success_rate: float = 0.0
    policy_violation_count: int = 0
    average_steps: float = 0.0
    average_wait_time_ms: float = 0.0


class WorkflowAuditRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    execution_id: UUID | None
    conversation_id: UUID | None
    event_type: str
    payload: dict[str, Any] | None
    operator: str | None
    occurred_at: datetime
