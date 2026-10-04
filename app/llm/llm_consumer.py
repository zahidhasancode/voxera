"""LLM consumer: streams tokens for one user turn and hands out speakable segments."""

import asyncio
from typing import Awaitable, Callable, Optional, Sequence

from app.core.logger import get_logger
from app.llm.sentence_chunker import SentenceChunker
from app.llm.streaming_engine import StreamToken, StreamingLLMEngine

logger = get_logger(__name__)

# WebSocket event types
LLM_PARTIAL = "llm_partial"
LLM_FINAL = "llm_final"
LLM_CANCELLED = "llm_cancelled"

# Outcome passed to on_complete
COMPLETED = "completed"
CANCELLED = "cancelled"
FAILED = "failed"

SegmentCallback = Callable[[str], Awaitable[None]]
CompleteCallback = Callable[[str, str], Awaitable[None]]


class LLMConsumer:
    """Runs the streaming LLM for a final transcript.

    - Emits llm_partial per token, then llm_final (or llm_cancelled).
    - Calls on_segment for every completed sentence while the stream is still
      running, so speech can start before the answer is finished.
    - Calls on_complete(text, outcome) exactly once per generation.
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
            engine: Streaming LLM engine (mock or a real provider).
            send_json: Async callback to send a JSON-serializable dict to the client.
            conversation_id: Optional conversation ID for event payloads.
        """
        self.engine = engine
        self.send_json = send_json
        self.conversation_id = conversation_id or ""
        self._task: Optional[asyncio.Task] = None

    @property
    def is_generating(self) -> bool:
        return self._task is not None and not self._task.done()

    def cancel(self) -> None:
        """Cancel in-flight LLM generation (idempotent)."""
        if self._task and not self._task.done():
            self._task.cancel()
            logger.debug(
                "LLM generation task cancelled",
                extra_fields={"conversation_id": self.conversation_id},
            )

    async def aclose(self) -> None:
        """Cancel and wait for the generation task to finish its cleanup."""
        task = self._task
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def _safe_send(self, payload: dict) -> None:
        try:
            await self.send_json(payload)
        except Exception:  # the socket may already be closed
            pass

    async def start_generation(
        self,
        transcript: str,
        utterance_id: str,
        *,
        history: Optional[Sequence[dict]] = None,
        on_first_token: Optional[Callable[[], None]] = None,
        on_segment: Optional[SegmentCallback] = None,
        on_complete: Optional[CompleteCallback] = None,
    ) -> None:
        """Start streaming the reply to a final transcript.

        Args:
            transcript: Final user transcript.
            utterance_id: Utterance ID for event correlation.
            history: Earlier turns ({"role", "content"}), oldest first.
            on_first_token: Called when the first token arrives.
            on_segment: Awaited with each completed sentence (for TTS).
            on_complete: Awaited with (full_text, outcome) when the stream ends;
                outcome is "completed", "cancelled" or "failed".
        """
        self.cancel()
        history_snapshot = list(history or [])

        async def _run() -> None:
            chunker = SentenceChunker()
            parts: list[str] = []
            outcome = COMPLETED
            try:
                async for st in self.engine.stream(
                    transcript,
                    utterance_id=utterance_id,
                    conversation_id=self.conversation_id,
                    history=history_snapshot,
                ):
                    if not isinstance(st, StreamToken):
                        continue
                    if not parts and on_first_token:
                        on_first_token()
                    parts.append(st.token)
                    await self.send_json({
                        "type": LLM_PARTIAL,
                        "utterance_id": utterance_id,
                        "conversation_id": self.conversation_id,
                        "token": st.token,
                        "token_index": st.token_index,
                        "accumulated": "".join(parts),
                    })
                    if on_segment:
                        for segment in chunker.feed(st.token):
                            await on_segment(segment)
                rest = chunker.flush()
                if rest and on_segment:
                    await on_segment(rest)
                m = self.engine.last_metrics()
                await self.send_json({
                    "type": LLM_FINAL,
                    "utterance_id": utterance_id,
                    "conversation_id": self.conversation_id,
                    "text": "".join(parts),
                    "metrics": m.to_dict(),
                })
                logger.info(
                    "LLM stream completed",
                    extra_fields={
                        "utterance_id": utterance_id,
                        "conversation_id": self.conversation_id,
                        "token_count": m.token_count,
                        "time_to_first_token_ms": m.time_to_first_token_ms,
                        "total_generation_ms": m.total_generation_ms,
                    },
                )
            except asyncio.CancelledError:
                outcome = CANCELLED
                await self._safe_send({
                    "type": LLM_CANCELLED,
                    "utterance_id": utterance_id,
                    "conversation_id": self.conversation_id,
                    "partial_text": "".join(parts),
                    "metrics": self.engine.last_metrics().to_dict(),
                })
                logger.info(
                    "LLM stream cancelled",
                    extra_fields={"utterance_id": utterance_id, "conversation_id": self.conversation_id},
                )
            except Exception as exc:
                outcome = FAILED
                logger.error(
                    "LLM stream failed",
                    extra_fields={"utterance_id": utterance_id, "conversation_id": self.conversation_id, "error": str(exc)},
                    exc_info=True,
                )
                await self._safe_send({"type": "error", "code": "llm_failed", "message": "The language model request failed"})
            finally:
                if on_complete:
                    try:
                        await on_complete("".join(parts), outcome)
                    except Exception:
                        logger.error("LLM completion callback failed", exc_info=True)

        self._task = asyncio.create_task(_run())
