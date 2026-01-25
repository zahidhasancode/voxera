"""Streaming LLM engine with async generator, cancellation, and latency instrumentation.

Designed for pluggable backends: Mock (default), OpenAI Realtime, vLLM, Triton Inference Server.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StreamToken:
    """A single token yielded by the streaming LLM."""

    token: str
    token_index: int


@dataclass
class LLMGenerationMetrics:
    """Latency and throughput metrics for one LLM generation."""

    time_to_first_token_ms: float = 0.0
    total_generation_ms: float = 0.0
    token_count: int = 0
    tokens_per_second: float = 0.0

    def to_dict(self) -> dict:
        """Serialize for WebSocket/JSON."""
        return {
            "time_to_first_token_ms": round(self.time_to_first_token_ms, 2),
            "total_generation_ms": round(self.total_generation_ms, 2),
            "token_count": self.token_count,
            "tokens_per_second": round(self.tokens_per_second, 2),
        }


class StreamingLLMEngine(ABC):
    """Abstract streaming LLM engine.

    Implementations: MockStreamingLLMEngine, OpenAI Realtime, vLLM, Triton.
    """

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[StreamToken]:
        """Stream tokens for the given prompt.

        Yields StreamToken. Cancellation (e.g. barge-in) is delivered by the
        event loop when the consuming task is cancelled; implementations
        should use await asyncio.sleep(...) or similar to allow delivery.

        After the generator exits (normally or cancelled), metrics are
        available via last_metrics().

        Args:
            prompt: User transcript or full prompt.
            utterance_id: Optional utterance ID for tracing.
            conversation_id: Optional conversation ID for tracing.

        Yields:
            StreamToken for each token.
        """
        ...

    def last_metrics(self) -> LLMGenerationMetrics:
        """Return metrics from the most recent stream() run.

        Valid after the async iterator is exhausted or cancelled.
        """
        return getattr(self, "_last_metrics", None) or LLMGenerationMetrics()


class MockStreamingLLMEngine(StreamingLLMEngine):
    """Mock streaming LLM for development and testing.

    - Emits tokens every 20–40 ms to simulate real LLM latency.
    - Supports interruption via asyncio cancellation.
    - Produces a deterministic mock response from the prompt.
    """

    def __init__(
        self,
        min_token_delay_ms: float = 20.0,
        max_token_delay_ms: float = 40.0,
        mock_response_template: str = "You said: \"{prompt}\". Here is a concise response.",
    ):
        """Initialize mock engine.

        Args:
            min_token_delay_ms: Minimum delay between tokens (ms).
            max_token_delay_ms: Maximum delay between tokens (ms).
            mock_response_template: Template for mock reply; {prompt} is replaced.
        """
        self.min_token_delay_ms = min_token_delay_ms
        self.max_token_delay_ms = max_token_delay_ms
        self.mock_response_template = mock_response_template
        self._last_metrics: LLMGenerationMetrics = LLMGenerationMetrics()

    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[StreamToken]:
        """Stream mock tokens with 20–40 ms delay per token."""
        text = self.mock_response_template.format(prompt=prompt or "(silence)")
        tokens = text.replace(".", " . ").replace(",", " , ").split()
        if not tokens:
            tokens = ["(no", "input)"]

        start = time.monotonic()
        first_token_time: Optional[float] = None
        token_count = 0

        try:
            for i, t in enumerate(tokens):
                delay_ms = random.uniform(
                    self.min_token_delay_ms,
                    self.max_token_delay_ms,
                )
                await asyncio.sleep(delay_ms / 1000.0)

                if first_token_time is None:
                    first_token_time = time.monotonic()

                token_count += 1
                yield StreamToken(token=t + (" " if i < len(tokens) - 1 else ""), token_index=i)

        except asyncio.CancelledError:
            logger.info(
                "Mock LLM stream cancelled (barge-in)",
                extra_fields={
                    "utterance_id": utterance_id,
                    "conversation_id": conversation_id,
                    "tokens_emitted": token_count,
                },
            )
            raise
        finally:
            end = time.monotonic()
            ttft_ms = (first_token_time - start) * 1000.0 if first_token_time else 0.0
            total_ms = (end - start) * 1000.0
            tps = (token_count / (total_ms / 1000.0)) if total_ms > 0 else 0.0
            self._last_metrics = LLMGenerationMetrics(
                time_to_first_token_ms=ttft_ms,
                total_generation_ms=total_ms,
                token_count=token_count,
                tokens_per_second=tps,
            )

    def last_metrics(self) -> LLMGenerationMetrics:
        return self._last_metrics
