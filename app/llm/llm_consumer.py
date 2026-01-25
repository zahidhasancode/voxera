"""LLM consumer: consumes final transcripts, streams tokens, and sends WebSocket events."""

import asyncio
from typing import Awaitable, Callable, Optional

from app.core.logger import get_logger
from app.llm.streaming_engine import LLMGenerationMetrics, StreamToken, StreamingLLMEngine

logger = get_logger(__name__)


async def _invoke(cb: Optional[Callable[[], object]]) -> None:
    if not cb:
        return
    if asyncio.iscoroutinefunction(cb):
        await cb()  # type: ignore[misc]
    else:
        cb()


# WebSocket event types
LLM_PARTIAL = "llm_partial"
LLM_FINAL = "llm_final"
LLM_CANCELLED = "llm_cancelled"


def _metrics_to_payload(m: LLMGenerationMetrics) -> dict:
    return m.to_dict()


class LLMConsumer:
    """Consumes final transcripts, runs the streaming LLM, and sends partial/final/cancelled over WebSocket.

    - Only starts generation when user turn ends (driven by on_user_turn_completed).
    - Cancels in-flight generation on new user speech or explicit interruption.
    - Emits: llm_partial (per token), llm_final (done + metrics), llm_cancelled (stopped + partial metrics).
    """

    def __init__(
        self,
        engine: StreamingLLMEngine,
        send_json: Callable[[dict], Awaitable[None]],
        *,
        conversation_id: Optional[str] = None,
    ):
        """Initialize consumer.

        Args:
            engine: Streaming LLM engine (mock, OpenAI, vLLM, Triton).
            send_json: Async callback to send a JSON-serializable dict over WebSocket.
            conversation_id: Optional conversation ID for event payloads.
        """
        self.engine = engine
        self.send_json = send_json
        self.conversation_id = conversation_id or ""
        self._task: Optional[asyncio.Task] = None
        self._accumulated: list[str] = []

    def cancel(self) -> None:
        """Cancel in-flight LLM generation (idempotent)."""
        if self._task and not self._task.done():
            self._task.cancel()
            logger.debug(
                "LLM generation task cancelled",
                extra_fields={"conversation_id": self.conversation_id},
            )

    async def start_generation(
        self,
        transcript: str,
        utterance_id: str,
        *,
        on_system_turn_start: Optional[Callable[[], object]] = None,
        on_system_turn_end: Optional[Callable[[], object]] = None,
        on_llm_final: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ) -> None:
        """Start streaming LLM for the given final transcript.

        Sends llm_partial for each token, llm_final when done, or llm_cancelled
        if cancelled. Uses engine.last_metrics() for metrics on completion or cancel.

        Args:
            transcript: Final user transcript.
            utterance_id: Utterance ID for event correlation.
            on_system_turn_start: Called when we begin generating (system turn started).
            on_system_turn_end: Called when we finish or are cancelled (system turn ended).
            on_llm_final: Called after llm_final is sent, with (text, utterance_id). Use for TTS.
        """
        self.cancel()

        await _invoke(on_system_turn_start)

        accumulated_text: list[str] = []

        async def _run() -> None:
            try:
                async for st in self.engine.stream(
                    transcript,
                    utterance_id=utterance_id,
                    conversation_id=self.conversation_id,
                ):
                    if not isinstance(st, StreamToken):
                        continue
                    accumulated_text.append(st.token)
                    await self.send_json({
                        "type": LLM_PARTIAL,
                        "utterance_id": utterance_id,
                        "conversation_id": self.conversation_id,
                        "token": st.token,
                        "token_index": st.token_index,
                        "accumulated": "".join(accumulated_text),
                    })

                full = "".join(accumulated_text)
                m = self.engine.last_metrics()
                await self.send_json({
                    "type": LLM_FINAL,
                    "utterance_id": utterance_id,
                    "conversation_id": self.conversation_id,
                    "text": full,
                    "metrics": _metrics_to_payload(m),
                })
                if on_llm_final:
                    await on_llm_final(full, utterance_id)
                logger.info(
                    "LLM stream completed",
                    extra_fields={
                        "utterance_id": utterance_id,
                        "conversation_id": self.conversation_id,
                        "token_count": m.token_count,
                        "time_to_first_token_ms": m.time_to_first_token_ms,
                        "total_generation_ms": m.total_generation_ms,
                        "tokens_per_second": m.tokens_per_second,
                    },
                )
            except asyncio.CancelledError:
                full = "".join(accumulated_text)
                m = self.engine.last_metrics()
                await self.send_json({
                    "type": LLM_CANCELLED,
                    "utterance_id": utterance_id,
                    "conversation_id": self.conversation_id,
                    "partial_text": full,
                    "metrics": _metrics_to_payload(m),
                })
                logger.info(
                    "LLM stream cancelled (barge-in)",
                    extra_fields={
                        "utterance_id": utterance_id,
                        "conversation_id": self.conversation_id,
                        "tokens_emitted": m.token_count,
                    },
                )
            finally:
                await _invoke(on_system_turn_end)

        self._task = asyncio.create_task(_run())
