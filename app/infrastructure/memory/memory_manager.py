"""MemoryManager implementation — single Planner entry point."""

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.config import settings
from app.core.enums import MemoryRole, SessionState
from app.core.exceptions import SessionNotFoundError
from app.memory.cache.base import MemoryCache
from app.memory.compression.compressor import MemoryCompressor
from app.memory.manager.memory_manager import MemoryManager
from app.memory.metrics.collector import MemoryMetricsCollector
from app.memory.repository import (
    ConversationRepository,
    ConversationSummaryRepository,
    ConversationTurnRepository,
    ToolExecutionRepository,
    WorkingMemoryRepository,
)
from app.memory.schemas import (
    AppendMessageRequest,
    AppendToolResultRequest,
    CreateSessionRequest,
    MemoryMetricsSnapshot,
    PlannerContext,
    SessionRead,
    StructuredSummary,
    SummaryRead,
    TurnRead,
    WorkingMemorySetRequest,
)
from app.memory.state.context_assembler import PlannerContextAssembler
from app.memory.summarizer.conversation_summarizer import ConversationSummarizer
from app.memory.validators.access_validator import MemoryAccessValidator
from app.infrastructure.memory.knowledge_memory import CachedKnowledgeMemory


class MemoryManagerImpl(MemoryManager):
    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        turns: ConversationTurnRepository,
        working_memory: WorkingMemoryRepository,
        tool_executions: ToolExecutionRepository,
        summaries: ConversationSummaryRepository,
        summarizer: ConversationSummarizer,
        compressor: MemoryCompressor,
        validator: MemoryAccessValidator,
        context_assembler: PlannerContextAssembler,
        knowledge_memory: CachedKnowledgeMemory,
        cache: MemoryCache,
    ) -> None:
        self._conversations = conversations
        self._turns = turns
        self._working_memory = working_memory
        self._tool_executions = tool_executions
        self._summaries = summaries
        self._summarizer = summarizer
        self._compressor = compressor
        self._validator = validator
        self._assembler = context_assembler
        self._knowledge_memory = knowledge_memory
        self._cache = cache

    async def create_session(self, request: CreateSessionRequest) -> SessionRead:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.MEMORY_SESSION_EXPIRY_HOURS)
        return await self._conversations.create(request, expires_at=expires_at)

    async def append_message(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendMessageRequest,
    ) -> TurnRead:
        session = await self._require_session(tenant_id, agent_id, conversation_id)
        turn_count = await self._turns.count(tenant_id, agent_id, conversation_id)
        turn = await self._turns.append(tenant_id, agent_id, conversation_id, turn_count, data)
        await self._conversations.increment_turn_count(tenant_id, agent_id, conversation_id)

        if data.language and data.language != session.language:
            await self._conversations.update_language(
                tenant_id, agent_id, conversation_id, data.language
            )

        await self._cache.delete(self._cache_ns(tenant_id, conversation_id), "context")

        if turn_count + 1 >= settings.MEMORY_SUMMARY_TURN_THRESHOLD:
            await self.generate_summary(tenant_id, agent_id, conversation_id)

        return turn

    async def append_tool_result(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: AppendToolResultRequest,
    ) -> None:
        await self._require_session(tenant_id, agent_id, conversation_id)
        await self._tool_executions.record(tenant_id, agent_id, conversation_id, data)
        await self._conversations.update_state(
            tenant_id, agent_id, conversation_id, SessionState.TOOL_EXECUTION
        )
        await self._cache.delete(self._cache_ns(tenant_id, conversation_id), "context")

    async def update_state(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        state: SessionState,
    ) -> SessionRead:
        await self._require_session(tenant_id, agent_id, conversation_id)
        updated = await self._conversations.update_state(tenant_id, agent_id, conversation_id, state)
        if updated is None:
            raise SessionNotFoundError(f"Session {conversation_id} not found")
        await self._cache.delete(self._cache_ns(tenant_id, conversation_id), "context")
        return updated

    async def set_working_memory(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        data: WorkingMemorySetRequest,
    ) -> None:
        await self._require_session(tenant_id, agent_id, conversation_id)
        key = data.key.value if hasattr(data.key, "value") else str(data.key)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.MEMORY_WORKING_MEMORY_TTL_SECONDS
        )
        await self._working_memory.upsert(
            tenant_id,
            agent_id,
            conversation_id,
            key,
            data.value,
            value_type=data.value_type,
            language=data.language,
            is_sensitive=data.is_sensitive,
            expires_at=expires_at,
        )
        await self._cache.delete(self._cache_ns(tenant_id, conversation_id), "context")

    async def get_context(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        retrieved_knowledge: list[str] | None = None,
        agent_configuration: dict | None = None,
        tenant_policies: dict | None = None,
    ) -> PlannerContext:
        metrics = MemoryMetricsCollector(str(tenant_id), str(conversation_id))
        cache_key = "context"
        ns = self._cache_ns(tenant_id, conversation_id)

        if settings.MEMORY_CACHE_TTL_SECONDS > 0:
            cached = await self._cache.get(ns, cache_key)
            if cached is not None:
                metrics.record_cache(True)
                return cached

        metrics.record_cache(False)
        session = await self._require_session(tenant_id, agent_id, conversation_id)
        turns = await self._turns.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=settings.MEMORY_MAX_TURNS_BEFORE_COMPRESS
        )
        summary_row = await self._summaries.get_latest(tenant_id, agent_id, conversation_id)
        summary = self._to_structured_summary(summary_row) if summary_row else None

        if settings.MEMORY_COMPRESSION_ENABLED:
            turns, summary, ratio = self._compressor.compress_turns(turns, summary)
            metrics.record_compression(ratio)

        wm_rows = await self._working_memory.list_by_conversation(tenant_id, agent_id, conversation_id)
        sensitive_keys = {r.memory_key for r in wm_rows if r.is_sensitive}
        wm_dict = {r.memory_key: r.value for r in wm_rows}
        wm_display = self._validator.redact_sensitive(wm_dict, sensitive_keys)

        tools = await self._tool_executions.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=20
        )
        knowledge = retrieved_knowledge or await self._knowledge_memory.get(
            tenant_id, agent_id, conversation_id
        )
        if retrieved_knowledge:
            await self._knowledge_memory.attach(tenant_id, agent_id, conversation_id, retrieved_knowledge)

        current_user_message = None
        for turn in reversed(turns):
            if turn.role == MemoryRole.USER:
                current_user_message = turn.message
                break

        context = self._assembler.assemble(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            current_state=SessionState(session.current_state),
            language=session.language,
            current_user_message=current_user_message,
            summary=summary,
            working_memory=wm_display,
            tool_results=tools,
            recent_turns=turns,
            retrieved_knowledge=knowledge,
            agent_configuration=agent_configuration,
            tenant_policies=tenant_policies,
        )

        size_bytes = sum(len(t.message.encode()) for t in turns)
        metrics.record_context(
            tokens=context.token_estimate,
            turns=len(turns),
            wm_entries=len(wm_rows),
            size_bytes=size_bytes,
        )
        metrics.emit()

        if settings.MEMORY_CACHE_TTL_SECONDS > 0:
            await self._cache.set(ns, cache_key, context, ttl_seconds=settings.MEMORY_CACHE_TTL_SECONDS)

        return context

    async def generate_summary(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> StructuredSummary:
        started = time.monotonic()
        session = await self._require_session(tenant_id, agent_id, conversation_id)
        turns = await self._turns.list_by_conversation(tenant_id, agent_id, conversation_id, limit=500)
        summary = await self._summarizer.summarize(turns, language=session.language)
        await self._summaries.save(
            tenant_id, agent_id, conversation_id, summary, turn_count=len(turns)
        )
        await self._cache.delete(self._cache_ns(tenant_id, conversation_id), "summary")
        elapsed_ms = int((time.monotonic() - started) * 1000)
        summary = summary.model_copy()
        return summary

    async def get_summary(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> StructuredSummary | None:
        await self._require_session(tenant_id, agent_id, conversation_id, allow_completed=True)
        row = await self._summaries.get_latest(tenant_id, agent_id, conversation_id)
        return self._to_structured_summary(row) if row else None

    async def clear_session(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> None:
        await self._require_session(tenant_id, agent_id, conversation_id, allow_completed=True)
        await self._working_memory.delete_by_conversation(tenant_id, agent_id, conversation_id)
        await self._cache.clear_namespace(self._cache_ns(tenant_id, conversation_id))
        await self._conversations.mark_completed(tenant_id, agent_id, conversation_id)

    async def archive(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead:
        await self.clear_session(tenant_id, agent_id, conversation_id)
        archived = await self._conversations.mark_archived(tenant_id, agent_id, conversation_id)
        if archived is None:
            raise SessionNotFoundError(f"Session {conversation_id} not found")
        return archived

    async def get_session(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> SessionRead:
        return await self._require_session(tenant_id, agent_id, conversation_id, allow_completed=True)

    async def get_history(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        limit: int = 100,
    ) -> list[TurnRead]:
        await self._require_session(tenant_id, agent_id, conversation_id, allow_completed=True)
        return await self._turns.list_by_conversation(
            tenant_id, agent_id, conversation_id, limit=limit
        )

    async def get_metrics(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> MemoryMetricsSnapshot:
        session = await self._require_session(tenant_id, agent_id, conversation_id, allow_completed=True)
        turns = await self._turns.list_by_conversation(tenant_id, agent_id, conversation_id, limit=500)
        wm = await self._working_memory.list_by_conversation(tenant_id, agent_id, conversation_id)
        size_bytes = sum(len(t.message.encode()) for t in turns)
        return MemoryMetricsSnapshot(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            memory_size_bytes=size_bytes,
            working_memory_entries=len(wm),
            conversation_turns=len(turns),
            cache_hit=self._cache.hits > 0 if hasattr(self._cache, "hits") else False,
            cache_miss=self._cache.misses > 0 if hasattr(self._cache, "misses") else False,
            average_context_tokens=sum(len(t.message) // 4 for t in turns),
        )

    async def _require_session(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        *,
        allow_completed: bool = False,
    ) -> SessionRead:
        session = await self._conversations.get(tenant_id, agent_id, conversation_id)
        if session is None:
            raise SessionNotFoundError(f"Session {conversation_id} not found")
        self._validator.validate_session_access(
            session,
            tenant_id=tenant_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            allow_completed=allow_completed,
        )
        return session

    @staticmethod
    def _cache_ns(tenant_id: UUID, conversation_id: UUID) -> str:
        return f"memory-{tenant_id}-{conversation_id}"

    @staticmethod
    def _to_structured_summary(row: SummaryRead) -> StructuredSummary:
        return StructuredSummary(
            customer_identity=row.customer_identity,
            conversation_goal=row.conversation_goal,
            resolved_items=row.resolved_items or [],
            pending_items=row.pending_items or [],
            collected_information=row.collected_information or {},
            summary_text=row.summary_text,
            token_estimate=row.token_estimate,
            language=row.language,
        )
