"""Enterprise RAG domain models and DTOs."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.core.schemas import SchemaBase


class RankingStrategyType(StrEnum):
    COSINE_SIMILARITY = "cosine_similarity"
    HYBRID = "hybrid"
    KEYWORD_BOOST = "keyword_boost"
    SEMANTIC_RERANK = "semantic_rerank"
    RECIPROCAL_RANK_FUSION = "reciprocal_rank_fusion"
    MMR = "mmr"


class MetadataFilterField(StrEnum):
    DEPARTMENT = "department"
    PRODUCT = "product"
    LANGUAGE = "language"
    VERSION = "version"
    DATE = "date"
    DOCUMENT = "document"
    KNOWLEDGE_TYPE = "knowledge_type"


class MetadataFilterSpec(SchemaBase):
    """Structured metadata filters — extensible for future dimensions."""

    department: str | None = None
    product: str | None = None
    language: str | None = None
    version: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    document: str | None = None
    knowledge_type: str | None = None
    extra: dict | None = Field(default=None, description="Future filter dimensions")

    def to_filter_dict(self) -> dict:
        result: dict = {}
        for field in (
            MetadataFilterField.DEPARTMENT,
            MetadataFilterField.PRODUCT,
            MetadataFilterField.LANGUAGE,
            MetadataFilterField.VERSION,
            MetadataFilterField.DOCUMENT,
            MetadataFilterField.KNOWLEDGE_TYPE,
        ):
            value = getattr(self, field.value, None)
            if value is not None:
                result[field.value] = value
        if self.extra:
            result.update(self.extra)
        return result


class ConversationTurn(SchemaBase):
    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str = Field(..., min_length=1, max_length=16384)
    timestamp: datetime | None = None


class ToolOutput(SchemaBase):
    tool_name: str
    output: str
    timestamp: datetime | None = None


class ConversationContext(SchemaBase):
    """Merged conversation state for prompt building."""

    current_turns: list[ConversationTurn] = Field(default_factory=list)
    conversation_summary: str | None = None
    agent_memory: str | None = None
    tool_outputs: list[ToolOutput] = Field(default_factory=list)


class NormalizedQuery(SchemaBase):
    original: str
    normalized: str
    language: str | None = None
    language_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class RankedChunk(SchemaBase):
    chunk_id: UUID
    source_id: UUID
    tenant_id: UUID
    content: str
    score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=0)
    metadata: dict = Field(default_factory=dict)
    source_title: str | None = None
    document: str | None = None
    page: int | None = None
    language: str | None = None
    vector_id: str | None = None


class RetrievalRequest(SchemaBase):
    tenant_id: UUID
    query: str = Field(..., min_length=1, max_length=8192)
    agent_id: UUID | None = None
    top_k: int | None = None
    min_similarity: float | None = None
    metadata_filter: MetadataFilterSpec | None = None
    source_ids: list[UUID] | None = None
    ranking_strategy: RankingStrategyType = RankingStrategyType.COSINE_SIMILARITY
    conversation: ConversationContext | None = None
    include_prompt: bool = False


class RetrievalResponse(SchemaBase):
    tenant_id: UUID
    agent_id: UUID | None = None
    query: NormalizedQuery
    chunks: list[RankedChunk]
    total_candidates: int
    average_similarity: float
    retrieval_latency_ms: int
    embedding_latency_ms: int
    ranking_latency_ms: int
    cache_hit: bool = False
    validated: bool = False


class BuiltContext(SchemaBase):
    """Compressed, deduplicated context ready for prompt injection."""

    tenant_id: UUID
    agent_id: UUID | None = None
    sections: list[str]
    merged_text: str
    token_estimate: int
    chunk_count: int
    deduplicated_count: int
    build_latency_ms: int


class PlannerPrompt(SchemaBase):
    """Optimized prompt for the Planner LLM — never contains raw documents."""

    system_prompt: str
    knowledge_context: str
    conversation_summary: str | None
    current_user_query: str
    safety_instructions: str
    tool_availability: str
    full_prompt: str
    token_estimate: int
    build_latency_ms: int


class EnterpriseRAGResult(SchemaBase):
    """Complete RAG pipeline output."""

    retrieval: RetrievalResponse
    context: BuiltContext
    prompt: PlannerPrompt | None = None
    metrics: dict = Field(default_factory=dict)
