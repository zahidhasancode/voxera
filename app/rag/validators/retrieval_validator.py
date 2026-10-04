"""Retrieval validation — security gate before LLM injection."""

from uuid import UUID

from app.core.config import settings
from app.core.enums import AgentStatus, KnowledgeSourceStatus
from app.core.exceptions import (
    CrossTenantAccessError,
    RetrievalValidationError,
    UnauthorizedAgentAccessError,
)
from app.rag.interfaces.models import BuiltContext, RetrievalRequest, RetrievalResponse
from app.rag.validators.sanitizer import PromptInjectionSanitizer


class RetrievalValidator:
    """
    Validates retrieved context before it reaches the LLM.

    Checks:
    - Tenant isolation
    - Agent authorization
    - Knowledge source active (READY)
    - Similarity threshold
    - Language compatibility
    - No duplicate chunks
    - No prompt injection in content
    """

    def __init__(self, sanitizer: PromptInjectionSanitizer | None = None) -> None:
        self._sanitizer = sanitizer or PromptInjectionSanitizer()

    def validate_retrieval(
        self,
        request: RetrievalRequest,
        response: RetrievalResponse,
        *,
        agent_status: AgentStatus | None = None,
        agent_tenant_id: UUID | None = None,
        agent_language: str | None = None,
        source_statuses: dict[UUID, KnowledgeSourceStatus] | None = None,
    ) -> None:
        violations: list[str] = []

        if response.tenant_id != request.tenant_id:
            raise CrossTenantAccessError(
                "Retrieval response tenant does not match request",
                violations=["tenant_mismatch"],
            )

        if request.agent_id and agent_tenant_id and agent_tenant_id != request.tenant_id:
            raise UnauthorizedAgentAccessError(
                "Agent does not belong to requesting tenant",
                violations=["agent_tenant_mismatch"],
            )

        if request.agent_id and agent_status and agent_status != AgentStatus.ACTIVE:
            violations.append(f"agent_not_active:{agent_status.value}")

        min_sim = request.min_similarity or settings.RAG_MIN_SIMILARITY_THRESHOLD
        seen_chunks: set[UUID] = set()

        for chunk in response.chunks:
            if chunk.tenant_id != request.tenant_id:
                raise CrossTenantAccessError(
                    f"Chunk {chunk.chunk_id} belongs to tenant {chunk.tenant_id}",
                    violations=["cross_tenant_chunk"],
                )

            if chunk.chunk_id in seen_chunks:
                violations.append(f"duplicate_chunk:{chunk.chunk_id}")
            seen_chunks.add(chunk.chunk_id)

            if chunk.score < min_sim:
                violations.append(f"below_similarity_threshold:{chunk.chunk_id}:{chunk.score}")

            if source_statuses and chunk.source_id in source_statuses:
                status = source_statuses[chunk.source_id]
                if status != KnowledgeSourceStatus.READY:
                    violations.append(f"inactive_source:{chunk.source_id}:{status.value}")

            if agent_language and chunk.language and not self._language_compatible(
                agent_language, chunk.language
            ):
                violations.append(
                    f"language_mismatch:{chunk.chunk_id}:{chunk.language} vs {agent_language}"
                )

            if self._sanitizer.contains_injection(chunk.content):
                violations.append(f"prompt_injection_detected:{chunk.chunk_id}")

        if violations:
            raise RetrievalValidationError(
                "Retrieval validation failed",
                violations=violations,
            )

    def validate_context(
        self,
        request: RetrievalRequest,
        context: BuiltContext,
    ) -> None:
        if context.tenant_id != request.tenant_id:
            raise CrossTenantAccessError("Context tenant mismatch")
        if request.agent_id and context.agent_id and context.agent_id != request.agent_id:
            raise UnauthorizedAgentAccessError("Context agent mismatch")
        if self._sanitizer.contains_injection(context.merged_text):
            raise RetrievalValidationError(
                "Built context contains prompt injection patterns",
                violations=["context_injection"],
            )

    @staticmethod
    def _language_compatible(agent_lang: str, chunk_lang: str) -> bool:
        agent_base = agent_lang.split("-")[0].lower()
        chunk_base = chunk_lang.split("-")[0].lower()
        return agent_base == chunk_base
