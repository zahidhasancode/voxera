"""Unit tests for MemoryManager with mocked repositories."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.enums import ConversationStatus, MemoryRole, SessionState
from app.infrastructure.memory.memory_manager import MemoryManagerImpl
from app.memory.cache.base import InMemoryMemoryCache
from app.memory.compression.compressor import MemoryCompressor
from app.memory.schemas import (
    AppendMessageRequest,
    AppendToolResultRequest,
    CreateSessionRequest,
    SessionRead,
    WorkingMemorySetRequest,
)
from app.memory.state.context_assembler import PlannerContextAssembler
from app.memory.summarizer.conversation_summarizer import StructuredConversationSummarizer
from app.memory.validators.access_validator import MemoryAccessValidator
from app.infrastructure.memory.knowledge_memory import CachedKnowledgeMemory


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def agent_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


def _session(tenant_id, agent_id, conversation_id):
    now = datetime.now(timezone.utc)
    return SessionRead(
        id=conversation_id,
        tenant_id=tenant_id,
        agent_id=agent_id,
        status=ConversationStatus.ACTIVE,
        current_state=SessionState.CALL_STARTED,
        language="en",
        turn_count=0,
        started_at=now,
        ended_at=None,
        expires_at=now + timedelta(hours=24),
        metadata=None,
        created_at=now,
        updated_at=now,
    )


def _manager(conversations, turns, wm, tools, summaries):
    cache = InMemoryMemoryCache()
    return MemoryManagerImpl(
        conversations=conversations,
        turns=turns,
        working_memory=wm,
        tool_executions=tools,
        summaries=summaries,
        summarizer=StructuredConversationSummarizer(),
        compressor=MemoryCompressor(),
        validator=MemoryAccessValidator(),
        context_assembler=PlannerContextAssembler(),
        knowledge_memory=CachedKnowledgeMemory(cache),
        cache=cache,
    )


@pytest.mark.asyncio
async def test_create_session(tenant_id, agent_id):
    conv_repo = AsyncMock()
    conv_repo.create = AsyncMock(return_value=_session(tenant_id, agent_id, uuid4()))
    manager = _manager(conv_repo, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())

    session = await manager.create_session(
        CreateSessionRequest(tenant_id=tenant_id, agent_id=agent_id)
    )
    assert session.tenant_id == tenant_id
    assert session.agent_id == agent_id


@pytest.mark.asyncio
async def test_append_message_increments_turns(tenant_id, agent_id, conversation_id):
    session = _session(tenant_id, agent_id, conversation_id)
    conv_repo = AsyncMock()
    conv_repo.get = AsyncMock(return_value=session)
    conv_repo.increment_turn_count = AsyncMock()

    turn = MagicMock()
    turn.role = MemoryRole.USER
    turn.message = "Hello"
    turn.model_validate = MagicMock(return_value=turn)

    turns_repo = AsyncMock()
    turns_repo.count = AsyncMock(return_value=0)
    turns_repo.append = AsyncMock(return_value=MagicMock(
        id=uuid4(), tenant_id=tenant_id, agent_id=agent_id,
        conversation_id=conversation_id, turn_index=0, role=MemoryRole.USER,
        message="Hello", language="en", latency_ms=None,
        tool_calls=None, reasoning_steps=None,
        created_at=session.created_at, updated_at=session.updated_at,
    ))

    summaries = AsyncMock()
    summaries.get_latest = AsyncMock(return_value=None)
    summaries.save = AsyncMock()

    manager = _manager(conv_repo, turns_repo, AsyncMock(), AsyncMock(), summaries)
    result = await manager.append_message(
        tenant_id, agent_id, conversation_id,
        AppendMessageRequest(role=MemoryRole.USER, message="Hello"),
    )
    assert result.message == "Hello"
    conv_repo.increment_turn_count.assert_awaited_once()


@pytest.mark.asyncio
async def test_working_memory_cleared_on_session_clear(tenant_id, agent_id, conversation_id):
    session = _session(tenant_id, agent_id, conversation_id)
    conv_repo = AsyncMock()
    conv_repo.get = AsyncMock(return_value=session)
    conv_repo.mark_completed = AsyncMock(return_value=session)

    wm_repo = AsyncMock()
    wm_repo.delete_by_conversation = AsyncMock(return_value=2)

    manager = _manager(conv_repo, AsyncMock(), wm_repo, AsyncMock(), AsyncMock())
    await manager.clear_session(tenant_id, agent_id, conversation_id)
    wm_repo.delete_by_conversation.assert_awaited_once()


@pytest.mark.asyncio
async def test_tenant_isolation_rejects_mismatch(tenant_id, agent_id, conversation_id):
    other_tenant = uuid4()
    session = _session(other_tenant, agent_id, conversation_id)
    conv_repo = AsyncMock()
    conv_repo.get = AsyncMock(return_value=session)

    manager = _manager(conv_repo, AsyncMock(), AsyncMock(), AsyncMock(), AsyncMock())
    from app.core.exceptions import CrossTenantMemoryError

    with pytest.raises(CrossTenantMemoryError):
        await manager.get_session(tenant_id, agent_id, conversation_id)
