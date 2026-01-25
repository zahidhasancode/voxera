"""TTS consumer: drives streaming TTS and sends raw PCM bytes to the client."""

import asyncio
from typing import Awaitable, Callable, Optional

from app.core.logger import get_logger
from app.tts.streaming_engine import StreamingTTSEngine

logger = get_logger(__name__)


class TTSConsumer:
    """Drives streaming TTS and sends PCM16 frames via send_bytes.

    - start_speaking(text, utterance_id) runs the engine and streams frames.
    - append_text(token) is a placeholder for future incremental TTS.
    - stop() cancels in-flight TTS and clears buffer.
    - No TurnManager wiring yet.
    """

    def __init__(
        self,
        engine: StreamingTTSEngine,
        send_bytes: Callable[[bytes], Awaitable[None]],
        send_json: Callable[[dict], Awaitable[None]],
        *,
        conversation_id: str = "",
    ):
        """Initialize consumer.

        Args:
            engine: Streaming TTS engine (mock or real).
            send_bytes: Async callback to send raw bytes (e.g. WebSocket send).
            send_json: Async callback to send JSON (e.g. for tts_metrics).
            conversation_id: Conversation ID for logging.
        """
        self.engine = engine
        self.send_bytes = send_bytes
        self.send_json = send_json
        self.conversation_id = conversation_id or ""
        self._task: Optional[asyncio.Task] = None
        self._current_utterance_id: Optional[str] = None
        self._buffer: list[str] = []
        self._lock: asyncio.Lock = asyncio.Lock()

    def _cancel_task(self) -> None:
        """Cancel in-flight TTS task (idempotent)."""
        if self._task and not self._task.done():
            self._task.cancel()
            logger.debug(
                "TTS task cancelled",
                extra_fields={"conversation_id": self.conversation_id},
            )

    async def start_speaking(self, text: str, utterance_id: str) -> None:
        """Start streaming TTS for the given text.

        Cancels any existing TTS, clears buffer, sets utterance_id, and
        creates a task to stream frames via send_bytes.

        Args:
            text: Full text to synthesize.
            utterance_id: Utterance ID for correlation.
        """
        self._cancel_task()
        async with self._lock:
            self._buffer.clear()
            self._current_utterance_id = utterance_id

        logger.info(
            "TTS start_speaking",
            extra_fields={
                "conversation_id": self.conversation_id,
                "utterance_id": utterance_id,
                "text_length": len(text),
            },
        )

        self._task = asyncio.create_task(self._run(text, utterance_id))

    async def append_text(self, token: str) -> None:
        """Append token to buffer. Placeholder for future incremental TTS.

        Does not stream to the TTS engine; full text only for now.
        """
        async with self._lock:
            self._buffer.append(token)

    async def stop(self) -> None:
        """Cancel any in-flight TTS task and clear buffer. Idempotent."""
        self._cancel_task()
        async with self._lock:
            self._buffer.clear()
        logger.debug(
            "TTS stop",
            extra_fields={"conversation_id": self.conversation_id},
        )

    async def _run(self, text: str, utterance_id: str) -> None:
        """Stream TTS frames from engine to send_bytes."""
        my_task = asyncio.current_task()
        frame_count = 0

        try:
            async for frame in self.engine.stream(text, utterance_id=utterance_id):
                await self.send_bytes(frame)
                frame_count += 1

            logger.info(
                "TTS stream completed",
                extra_fields={
                    "conversation_id": self.conversation_id,
                    "utterance_id": utterance_id,
                    "frames_sent": frame_count,
                },
            )
        except asyncio.CancelledError:
            logger.info(
                "TTS stream cancelled",
                extra_fields={
                    "conversation_id": self.conversation_id,
                    "utterance_id": utterance_id,
                    "frames_sent": frame_count,
                },
            )
        finally:
            if self._task is my_task:
                self._task = None
            async with self._lock:
                if self._current_utterance_id == utterance_id:
                    self._current_utterance_id = None
            metrics = self.engine.last_metrics()
            await self.send_json({
                "type": "tts_metrics",
                "utterance_id": utterance_id,
                "conversation_id": self.conversation_id,
                "metrics": metrics.to_dict(),
            })
