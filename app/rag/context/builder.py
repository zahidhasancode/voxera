"""Context builder — merge, deduplicate, and budget tokens."""

import hashlib
import time

from app.core.config import settings
from app.rag.interfaces.models import BuiltContext, RankedChunk


class ContextBuilder:
    """
    Compresses ranked chunks into a bounded context block.

    Responsibilities:
    - Merge chunks in rank order
    - Remove duplicates (content hash)
    - Token budgeting
    - Preserve document ordering
    """

    def __init__(self, max_tokens: int | None = None) -> None:
        self._max_tokens = max_tokens or settings.RAG_MAX_CONTEXT_TOKENS

    async def build(
        self,
        chunks: list[RankedChunk],
        *,
        tenant_id,
        agent_id=None,
    ) -> BuiltContext:
        started = time.monotonic()
        seen_hashes: set[str] = set()
        sections: list[str] = []
        deduplicated = 0
        token_count = 0

        ordered = sorted(chunks, key=lambda c: (c.rank, -c.score))
        for chunk in ordered:
            content_hash = hashlib.sha256(chunk.content.encode()).hexdigest()
            if content_hash in seen_hashes:
                deduplicated += 1
                continue
            seen_hashes.add(content_hash)

            excerpt = self._format_excerpt(chunk)
            excerpt_tokens = self._estimate_tokens(excerpt)
            if token_count + excerpt_tokens > self._max_tokens:
                break

            sections.append(excerpt)
            token_count += excerpt_tokens

        merged = "\n\n---\n\n".join(sections)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        return BuiltContext(
            tenant_id=tenant_id,
            agent_id=agent_id,
            sections=sections,
            merged_text=merged,
            token_estimate=token_count,
            chunk_count=len(chunks),
            deduplicated_count=deduplicated,
            build_latency_ms=elapsed_ms,
        )

    @staticmethod
    def _format_excerpt(chunk: RankedChunk) -> str:
        parts = [f"[Source: {chunk.source_title or chunk.document or chunk.source_id}]"]
        if chunk.page is not None:
            parts.append(f"[Page: {chunk.page}]")
        if chunk.language:
            parts.append(f"[Lang: {chunk.language}]")
        parts.append(chunk.content.strip())
        return " ".join(parts)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)
