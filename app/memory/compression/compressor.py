"""Memory compression engine."""

import hashlib
import time

from app.core.config import settings
from app.core.logger import get_logger
from app.memory.schemas import StructuredSummary, TurnRead

logger = get_logger(__name__)


class MemoryCompressor:
    """
    Compresses conversation history to stay within token budget.

    Rules:
    - Deduplicate identical messages
    - Drop low-value filler turns
    - Keep recent turns intact; older turns represented by summary
    """

    _FILLER = frozenset({"ok", "okay", "thanks", "thank you", "yes", "no", "hi", "hello", "bye"})

    def compress_turns(
        self,
        turns: list[TurnRead],
        summary: StructuredSummary | None,
        *,
        max_tokens: int | None = None,
    ) -> tuple[list[TurnRead], StructuredSummary | None, float]:
        max_tokens = max_tokens or settings.MEMORY_MAX_CONTEXT_TOKENS
        started = time.monotonic()
        original_count = len(turns)

        deduped = self._deduplicate(turns)
        filtered = self._remove_filler(deduped)

        token_count = sum(len(t.message) // 4 for t in filtered)
        if summary:
            token_count += summary.token_estimate

        if token_count <= max_tokens:
            ratio = 1.0 if original_count == 0 else len(filtered) / original_count
            return filtered, summary, ratio

        keep_recent = max(4, settings.MEMORY_SUMMARY_TURN_THRESHOLD // 2)
        compressed = filtered[-keep_recent:]
        ratio = len(compressed) / original_count if original_count else 1.0

        elapsed_ms = int((time.monotonic() - started) * 1000)
        logger.info(
            "Memory compressed",
            extra_fields={
                "original_turns": original_count,
                "compressed_turns": len(compressed),
                "compression_ratio": round(ratio, 3),
                "duration_ms": elapsed_ms,
                "event": "memory_compressed",
            },
        )
        return compressed, summary, ratio

    def _deduplicate(self, turns: list[TurnRead]) -> list[TurnRead]:
        seen: set[str] = set()
        result: list[TurnRead] = []
        for turn in turns:
            digest = hashlib.sha256(f"{turn.role}:{turn.message}".encode()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            result.append(turn)
        return result

    def _remove_filler(self, turns: list[TurnRead]) -> list[TurnRead]:
        return [t for t in turns if t.message.strip().lower() not in self._FILLER]
