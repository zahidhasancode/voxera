"""Memory observability metrics."""

import time

from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryMetricsCollector:
    def __init__(self, tenant_id: str, conversation_id: str) -> None:
        self.tenant_id = tenant_id
        self.conversation_id = conversation_id
        self.memory_size_bytes = 0
        self.summary_generation_ms = 0
        self.compression_ratio = 0.0
        self.cache_hit = False
        self.cache_miss = False
        self.average_context_tokens = 0
        self.working_memory_entries = 0
        self.conversation_turns = 0
        self._started = time.monotonic()

    def record_cache(self, hit: bool) -> None:
        self.cache_hit = hit
        self.cache_miss = not hit

    def record_summary(self, duration_ms: int) -> None:
        self.summary_generation_ms = duration_ms

    def record_compression(self, ratio: float) -> None:
        self.compression_ratio = ratio

    def record_context(self, *, tokens: int, turns: int, wm_entries: int, size_bytes: int) -> None:
        self.average_context_tokens = tokens
        self.conversation_turns = turns
        self.working_memory_entries = wm_entries
        self.memory_size_bytes = size_bytes

    def snapshot(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "conversation_id": self.conversation_id,
            "total_latency_ms": int((time.monotonic() - self._started) * 1000),
            "memory_size_bytes": self.memory_size_bytes,
            "summary_generation_ms": self.summary_generation_ms,
            "compression_ratio": round(self.compression_ratio, 4),
            "cache_hit": self.cache_hit,
            "cache_miss": self.cache_miss,
            "average_context_tokens": self.average_context_tokens,
            "working_memory_entries": self.working_memory_entries,
            "conversation_turns": self.conversation_turns,
            "event": "memory_metrics",
        }

    def emit(self) -> None:
        logger.info("Memory metrics", extra_fields=self.snapshot())
