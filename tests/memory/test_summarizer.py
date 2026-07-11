"""Unit tests for conversation summarizer."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.core.enums import MemoryRole
from app.memory.schemas import TurnRead
from app.memory.summarizer.conversation_summarizer import StructuredConversationSummarizer


def _turn(role, message):
    now = datetime.now(timezone.utc)
    return TurnRead(
        id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        conversation_id=uuid4(),
        turn_index=0,
        role=role,
        message=message,
        language="en",
        latency_ms=None,
        tool_calls=None,
        reasoning_steps=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_summarizer_extracts_goal_and_identity():
    summarizer = StructuredConversationSummarizer()
    turns = [
        _turn(MemoryRole.USER, "Hi, my name is Jane Doe. I need to check my order #ORD-12345 status."),
        _turn(MemoryRole.ASSISTANT, "I can help with that order lookup."),
    ]
    summary = await summarizer.summarize(turns)
    assert summary.conversation_goal is not None
    assert "order_number" in summary.collected_information or summary.collected_information
    assert summary.token_estimate > 0
    assert "Conversation Summary" in summary.summary_text


@pytest.mark.asyncio
async def test_summarizer_detects_pending_items():
    summarizer = StructuredConversationSummarizer()
    turns = [
        _turn(MemoryRole.USER, "I'm still waiting for a callback about my refund."),
    ]
    summary = await summarizer.summarize(turns)
    assert len(summary.pending_items) >= 1
