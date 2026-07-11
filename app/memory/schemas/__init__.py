"""Memory domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.enums import ConversationStatus, MemoryRole, SessionState, ToolExecutionStatus, WorkingMemoryKey
from app.core.schemas import SchemaBase, TenantScopedSchema, TimestampSchema


class CreateSessionRequest(TenantScopedSchema):
    agent_id: UUID
    language: str = Field(default="en", max_length=16)
    metadata: dict | None = None


class SessionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    agent_id: UUID
    status: ConversationStatus
    current_state: SessionState
    language: str
    turn_count: int
    started_at: datetime | None
    ended_at: datetime | None
    expires_at: datetime | None
    metadata: dict | None = Field(default=None, validation_alias="metadata_")


class AppendMessageRequest(SchemaBase):
    role: MemoryRole
    message: str = Field(..., min_length=1, max_length=32768)
    language: str | None = Field(default=None, max_length=16)
    latency_ms: int | None = Field(default=None, ge=0)
    tool_calls: list[dict] | None = None
    reasoning_steps: list[dict] | None = None


class TurnRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    conversation_id: UUID
    agent_id: UUID
    turn_index: int
    role: MemoryRole
    message: str
    language: str
    latency_ms: int | None
    tool_calls: list[dict] | None
    reasoning_steps: list[dict] | None


class AppendToolResultRequest(SchemaBase):
    tool_name: str = Field(..., min_length=1, max_length=128)
    arguments: dict | None = None
    execution_time_ms: int | None = Field(default=None, ge=0)
    status: ToolExecutionStatus = ToolExecutionStatus.SUCCESS
    result: str | None = None
    error: str | None = None


class ToolExecutionRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    conversation_id: UUID
    agent_id: UUID
    tool_name: str
    arguments: dict | None
    execution_time_ms: int | None
    status: ToolExecutionStatus
    result: str | None
    error: str | None
    executed_at: datetime | None


class UpdateStateRequest(SchemaBase):
    state: SessionState


class WorkingMemorySetRequest(SchemaBase):
    key: WorkingMemoryKey | str
    value: str = Field(..., max_length=4096)
    value_type: str = Field(default="string", max_length=32)
    language: str | None = None
    is_sensitive: bool = False


class WorkingMemoryRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    conversation_id: UUID
    agent_id: UUID
    memory_key: str
    value: str
    value_type: str
    language: str | None
    expires_at: datetime | None
    is_sensitive: bool


class StructuredSummary(SchemaBase):
    customer_identity: str | None = None
    conversation_goal: str | None = None
    resolved_items: list[str] = Field(default_factory=list)
    pending_items: list[str] = Field(default_factory=list)
    collected_information: dict = Field(default_factory=dict)
    summary_text: str = ""
    token_estimate: int = 0
    language: str = "en"


class SummaryRead(TimestampSchema, TenantScopedSchema):
    id: UUID
    conversation_id: UUID
    agent_id: UUID
    customer_identity: str | None
    conversation_goal: str | None
    resolved_items: list[str] | None
    pending_items: list[str] | None
    collected_information: dict | None
    summary_text: str
    token_estimate: int
    turn_count_at_summary: int
    language: str


class PlannerContext(SchemaBase):
    """Unified context object for the Planner LLM."""

    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    current_user_message: str | None = None
    conversation_summary: StructuredSummary | None = None
    working_memory: dict[str, str] = Field(default_factory=dict)
    retrieved_knowledge: list[str] = Field(default_factory=list)
    tool_results: list[ToolExecutionRead] = Field(default_factory=list)
    agent_configuration: dict = Field(default_factory=dict)
    tenant_policies: dict = Field(default_factory=dict)
    current_state: SessionState
    language: str
    recent_turns: list[TurnRead] = Field(default_factory=list)
    token_estimate: int = 0


class MemoryMetricsSnapshot(SchemaBase):
    conversation_id: UUID
    tenant_id: UUID
    memory_size_bytes: int = 0
    summary_generation_ms: int = 0
    compression_ratio: float = 0.0
    cache_hit: bool = False
    cache_miss: bool = False
    average_context_tokens: int = 0
    working_memory_entries: int = 0
    conversation_turns: int = 0
