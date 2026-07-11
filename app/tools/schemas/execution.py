"""Tool execution framework Pydantic schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.core.enums import ToolFrameworkExecutionStatus, ToolPermissionEffect
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class ToolParameterSchema(SchemaBase):
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = Field(default=False, alias="additionalProperties")


class ToolDefinitionRead(SchemaBase):
    """Tool metadata exposed to Planner."""

    slug: str
    name: str
    description: str
    parameters: dict[str, Any]
    permission_scope: str
    enabled: bool = True
    version: str = "1.0.0"


class ToolExecuteRequest(SchemaBase):
    tool_slug: str = Field(..., min_length=2, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)
    conversation_id: UUID | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)
    operator: str | None = Field(default=None, max_length=128)
    department: str | None = None
    role: str | None = None
    dry_run: bool = False


class ToolTestRequest(SchemaBase):
    tool_slug: str = Field(..., min_length=2, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(SchemaBase):
    """Structured result returned to Planner (and optionally forwarded to Memory)."""

    status: ToolFrameworkExecutionStatus
    tool_name: str
    tool_slug: str
    execution_time_ms: float
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    timestamp: datetime
    conversation_id: UUID | None = None
    tenant_id: UUID
    agent_id: UUID
    execution_id: UUID | None = None


class ToolExecutionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID | None
    tool_slug: str
    tool_name: str
    status: ToolFrameworkExecutionStatus
    arguments: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None
    execution_time_ms: float
    retry_count: int
    idempotency_key: str | None


class ToolPermissionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID | None
    tool_slug: str
    effect: ToolPermissionEffect
    department: str | None
    role: str | None
    max_executions_per_hour: int | None
    working_hours_start: str | None
    working_hours_end: str | None


class TenantToolConfigRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    tool_slug: str
    enabled: bool
    credentials_ref: str | None
    provider_config: dict[str, Any] | None
    rate_limit_per_minute: int | None
    timeout_seconds: float | None


class ToolAuditRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    conversation_id: UUID | None
    execution_id: UUID | None
    tool_slug: str
    status: str
    planner_request: dict[str, Any] | None
    validated_arguments: dict[str, Any] | None
    execution_result: dict[str, Any] | None
    execution_duration_ms: float | None
    operator: str | None
    error: str | None
    occurred_at: datetime


class ToolMetricsSnapshot(SchemaBase):
    total_executions: int = 0
    success_count: int = 0
    failure_count: int = 0
    permission_denied_count: int = 0
    validation_failure_count: int = 0
    average_latency_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    calls_by_tool: dict[str, int] = Field(default_factory=dict)
    success_rate: float = 0.0


class ToolExecutionContext(SchemaBase):
    """Runtime context passed to tool implementations."""

    tenant_id: UUID
    agent_id: UUID
    conversation_id: UUID | None = None
    tool_slug: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    provider_config: dict[str, Any] | None = None
    credentials_ref: str | None = None
    timeout_seconds: float = 30.0
    idempotency_key: str | None = None
