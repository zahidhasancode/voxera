"""RAG metrics collector."""

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from app.core.logger import get_logger

logger = get_logger(__name__)


class RetrievalMetricsCollector:
    """Structured metrics for the enterprise retrieval pipeline."""

    def __init__(self, tenant_id: str, agent_id: str | None = None) -> None:
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.retrieval_latency_ms = 0
        self.embedding_latency_ms = 0
        self.ranking_latency_ms = 0
        self.context_build_latency_ms = 0
        self.prompt_build_latency_ms = 0
        self.cache_hit = False
        self.cache_miss = False
        self.retrieved_chunk_count = 0
        self.average_similarity = 0.0
        self.prompt_token_count = 0
        self.context_token_count = 0
        self._started_at = time.monotonic()

    @asynccontextmanager
    async def measure(self, stage: str) -> AsyncGenerator[None, None]:
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            setattr(self, f"{stage}_latency_ms", elapsed_ms)
            logger.info(
                f"RAG stage {stage} completed",
                extra_fields={
                    "tenant_id": self.tenant_id,
                    "agent_id": self.agent_id,
                    "stage": stage,
                    "latency_ms": elapsed_ms,
                    "event": f"rag_{stage}_completed",
                },
            )

    def record_cache(self, hit: bool) -> None:
        self.cache_hit = hit
        self.cache_miss = not hit
        logger.info(
            "RAG cache access",
            extra_fields={
                "tenant_id": self.tenant_id,
                "cache_hit": hit,
                "event": "rag_cache_hit" if hit else "rag_cache_miss",
            },
        )

    def record_chunks(self, count: int, average_similarity: float) -> None:
        self.retrieved_chunk_count = count
        self.average_similarity = average_similarity

    def record_tokens(self, *, context_tokens: int, prompt_tokens: int) -> None:
        self.context_token_count = context_tokens
        self.prompt_token_count = prompt_tokens

    def snapshot(self) -> dict:
        total_ms = int((time.monotonic() - self._started_at) * 1000)
        return {
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "total_latency_ms": total_ms,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "embedding_latency_ms": self.embedding_latency_ms,
            "ranking_latency_ms": self.ranking_latency_ms,
            "context_build_latency_ms": self.context_build_latency_ms,
            "prompt_build_latency_ms": self.prompt_build_latency_ms,
            "cache_hit": self.cache_hit,
            "cache_miss": self.cache_miss,
            "retrieved_chunk_count": self.retrieved_chunk_count,
            "average_similarity": round(self.average_similarity, 4),
            "prompt_token_count": self.prompt_token_count,
            "context_token_count": self.context_token_count,
        }

    def emit_summary(self) -> None:
        logger.info(
            "RAG pipeline metrics",
            extra_fields={**self.snapshot(), "event": "rag_pipeline_metrics"},
        )
