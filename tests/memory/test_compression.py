"""Unit tests for memory compression."""

from datetime import datetime, timezone
from uuid import uuid4

from app.core.enums import MemoryRole
from app.memory.compression.compressor import MemoryCompressor
from app.memory.schemas import TurnRead


def _turn(message: str, idx: int = 0) -> TurnRead:
    now = datetime.now(timezone.utc)
    return TurnRead(
        id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        conversation_id=uuid4(),
        turn_index=idx,
        role=MemoryRole.USER,
        message=message,
        language="en",
        latency_ms=None,
        tool_calls=None,
        reasoning_steps=None,
        created_at=now,
        updated_at=now,
    )


def test_compressor_deduplicates_messages():
    compressor = MemoryCompressor()
    turns = [_turn("same message"), _turn("same message"), _turn("unique message")]
    compressed, _, ratio = compressor.compress_turns(turns, None, max_tokens=10000)
    assert len(compressed) == 2
    assert ratio < 1.0


def test_compressor_removes_filler():
    compressor = MemoryCompressor()
    turns = [_turn("ok"), _turn("What is my balance?")]
    compressed, _, _ = compressor.compress_turns(turns, None, max_tokens=10000)
    assert all(t.message.lower() != "ok" for t in compressed)


def test_compressor_truncates_under_token_budget():
    compressor = MemoryCompressor()
    turns = [_turn(f"message number {i} with content", i) for i in range(30)]
    compressed, _, ratio = compressor.compress_turns(turns, None, max_tokens=50)
    assert len(compressed) < len(turns)
    assert ratio < 1.0
