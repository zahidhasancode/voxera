"""Unit tests for ContextBuilder."""

import pytest
from uuid import uuid4

from app.rag.context.builder import ContextBuilder
from app.rag.interfaces.models import RankedChunk


@pytest.fixture
def tenant_id():
    return uuid4()


def _chunk(rank: int, content: str, score: float = 0.9) -> RankedChunk:
    return RankedChunk(
        chunk_id=uuid4(),
        source_id=uuid4(),
        tenant_id=uuid4(),
        content=content,
        score=score,
        rank=rank,
        metadata={"document": "manual.pdf", "page": 1},
        source_title="Product Manual",
        document="manual.pdf",
        page=1,
        language="en",
    )


@pytest.mark.asyncio
async def test_context_builder_merges_and_deduplicates(tenant_id):
    builder = ContextBuilder(max_tokens=2000)
    chunks = [
        _chunk(0, "Return policy is 30 days."),
        _chunk(1, "Return policy is 30 days."),  # duplicate
        _chunk(2, "Shipping takes 3-5 business days."),
    ]
    result = await builder.build(chunks, tenant_id=tenant_id)

    assert result.chunk_count == 3
    assert result.deduplicated_count == 1
    assert len(result.sections) == 2
    assert "Return policy" in result.merged_text
    assert result.token_estimate > 0


@pytest.mark.asyncio
async def test_context_builder_respects_token_budget(tenant_id):
    builder = ContextBuilder(max_tokens=20)
    chunks = [_chunk(i, f"short {i}", score=0.9 - i * 0.01) for i in range(5)]
    result = await builder.build(chunks, tenant_id=tenant_id)

    assert len(result.sections) >= 1
    assert result.token_estimate <= 20


@pytest.mark.asyncio
async def test_context_builder_preserves_rank_order(tenant_id):
    builder = ContextBuilder(max_tokens=5000)
    chunks = [
        _chunk(2, "Third priority content.", score=0.7),
        _chunk(0, "First priority content.", score=0.95),
        _chunk(1, "Second priority content.", score=0.85),
    ]
    result = await builder.build(chunks, tenant_id=tenant_id)
    assert result.sections[0].startswith("[Source:")
