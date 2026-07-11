"""Chunking strategy tests."""

from app.core.enums import ChunkStrategyType
from app.knowledge.chunking.models import ChunkConfig
from app.knowledge.chunking.strategy import ChunkingStrategy


def test_recursive_chunking_respects_size() -> None:
    text = "word " * 500
    strategy = ChunkingStrategy(ChunkConfig(chunk_size=200, chunk_overlap=20, strategy=ChunkStrategyType.RECURSIVE))
    chunks = strategy.chunk_text(text.strip())
    assert len(chunks) > 1
    assert all(len(c.content) <= 220 for c in chunks)


def test_sentence_chunking() -> None:
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    strategy = ChunkingStrategy(
        ChunkConfig(chunk_size=64, chunk_overlap=0, strategy=ChunkStrategyType.SENTENCE)
    )
    chunks = strategy.chunk_text(text)
    assert len(chunks) >= 2


def test_markdown_chunking_preserves_heading() -> None:
    text = "# Title\n\nIntro paragraph.\n\n## Section\n\nDetails here."
    strategy = ChunkingStrategy(ChunkConfig(chunk_size=500, strategy=ChunkStrategyType.MARKDOWN))
    chunks = strategy.chunk_text(text)
    assert any((c.metadata or {}).get("heading") for c in chunks)


def test_token_chunking() -> None:
    text = " ".join(f"token{i}" for i in range(100))
    strategy = ChunkingStrategy(
        ChunkConfig(maximum_tokens=32, strategy=ChunkStrategyType.TOKEN)
    )
    chunks = strategy.chunk_text(text)
    assert len(chunks) >= 3
    assert all(c.token_count is not None and c.token_count <= 32 for c in chunks)
