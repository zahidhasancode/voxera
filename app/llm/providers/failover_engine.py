"""LLM engine with primary/failover provider support."""

from __future__ import annotations

from typing import AsyncIterator, Optional, Sequence

from app.core.logger import get_logger
from app.llm.streaming_engine import LLMGenerationMetrics, StreamToken, StreamingLLMEngine

logger = get_logger(__name__)


class FailoverStreamingLLMEngine(StreamingLLMEngine):
    """Attempts primary provider, falls back to secondary on failure."""

    def __init__(self, primary: StreamingLLMEngine, secondary: StreamingLLMEngine | None = None) -> None:
        self._primary = primary
        self._secondary = secondary
        self._active = primary
        self._last_metrics = LLMGenerationMetrics()

    async def validate_connection(self) -> None:
        await self._primary.validate_connection()
        if self._secondary is not None:
            await self._secondary.validate_connection()

    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        history: Optional[Sequence[dict]] = None,
    ) -> AsyncIterator[StreamToken]:
        for engine in (self._primary, self._secondary):
            if engine is None:
                continue
            emitted = 0
            try:
                self._active = engine
                async for token in engine.stream(
                    prompt,
                    utterance_id=utterance_id,
                    conversation_id=conversation_id,
                    history=history,
                ):
                    emitted += 1
                    yield token
                self._last_metrics = engine.last_metrics()
                return
            except Exception as exc:
                if emitted:
                    # Part of the answer has already been streamed (and possibly spoken);
                    # starting again on another provider would repeat it.
                    raise
                logger.warning(
                    "LLM provider failed, trying failover",
                    extra_fields={
                        "provider": type(engine).__name__,
                        "error": str(exc),
                        "utterance_id": utterance_id,
                    },
                )
        raise RuntimeError("All configured LLM providers failed")

    def last_metrics(self) -> LLMGenerationMetrics:
        return self._active.last_metrics() if self._active else self._last_metrics
