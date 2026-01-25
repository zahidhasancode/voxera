"""STT consumer for streaming audio pipeline."""

import asyncio
from typing import Awaitable, Callable, Optional, Union

from app.core.logger import get_logger
from app.stt.engine import StreamingSTTEngine
from app.stt.models import TranscriptEvent

logger = get_logger(__name__)


class STTConsumer:
    """STT consumer that processes audio frames through STT engine.

    Subscribes to audio dispatcher and processes frames without blocking.
    Uses a bounded queue to handle backpressure.
    """

    def __init__(
        self,
        engine: StreamingSTTEngine,
        transcript_callback: Optional[
            Union[
                Callable[[TranscriptEvent], Awaitable[None]],
                Callable[[TranscriptEvent], None],
            ]
        ] = None,
        max_queue_size: int = 50,
    ):
        """Initialize STT consumer.

        Args:
            engine: StreamingSTTEngine instance
            transcript_callback: Async callback for transcript events
            max_queue_size: Maximum queue size for audio frames
        """
        self.engine = engine
        self.transcript_callback = transcript_callback
        self.max_queue_size = max_queue_size
        self._queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.frames_processed = 0
        self.frames_dropped = 0

    async def start(self) -> None:
        """Start STT consumer processing."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info(
            "STT consumer started",
            extra_fields={
                "max_queue_size": self.max_queue_size,
                "has_callback": self.transcript_callback is not None,
            },
        )

    async def stop(self) -> None:
        """Stop STT consumer and finalize any pending utterance."""
        if not self._running:
            return

        self._running = False

        # Finalize current utterance before stopping
        try:
            final_event = await self.engine.finalize_utterance()
            if final_event and self.transcript_callback:
                await self.transcript_callback(final_event)
        except Exception as e:
            logger.error(
                "Error finalizing utterance on stop",
                extra_fields={"error": str(e)},
            )

        # Signal shutdown
        await self._queue.put(None)

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("STT consumer did not stop gracefully, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info(
            "STT consumer stopped",
            extra_fields={
                "frames_processed": self.frames_processed,
                "frames_dropped": self.frames_dropped,
            },
        )

    async def process_frame(self, frame: bytes) -> bool:
        """Non-blocking enqueue of audio frame.

        Args:
            frame: Audio frame bytes (20ms PCM16)

        Returns:
            True if frame was queued, False if dropped due to backpressure
        """
        try:
            self._queue.put_nowait(frame)
            return True
        except asyncio.QueueFull:
            self.frames_dropped += 1
            logger.debug(
                "STT consumer queue full, dropping frame",
                extra_fields={
                    "queue_size": self._queue.qsize(),
                    "total_dropped": self.frames_dropped,
                },
            )
            return False

    async def _process_loop(self) -> None:
        """Main processing loop - pulls frames and processes through STT engine."""
        while self._running:
            try:
                frame = await self._queue.get()
                if frame is None:  # Shutdown signal
                    break

                # Log when frames are passed to engine (first few and periodically)
                if self.frames_processed < 5 or self.frames_processed % 25 == 0:
                    logger.debug(
                        "Audio frame passed to STT engine",
                        extra_fields={
                            "frame_size_bytes": len(frame) if frame else 0,
                            "frames_processed": self.frames_processed,
                            "queue_size": self._queue.qsize(),
                        },
                    )

                # Process frame through STT engine
                transcript_event = await self.engine.process_audio(frame)

                if transcript_event:
                    # Emit transcript event via callback
                    if self.transcript_callback:
                        try:
                            if asyncio.iscoroutinefunction(self.transcript_callback):
                                await self.transcript_callback(transcript_event)
                            else:
                                # Sync callback - wrap in task to avoid blocking
                                self.transcript_callback(transcript_event)
                        except Exception as e:
                            logger.error(
                                "Error in transcript callback",
                                extra_fields={
                                    "error": str(e),
                                    "event_type": transcript_event.type.value,
                                    "utterance_id": transcript_event.utterance_id,
                                },
                                exc_info=True,
                            )
                else:
                    # Log when no transcript is emitted (debug level)
                    if self.frames_processed < 10:
                        logger.debug(
                            "No transcript emitted for frame",
                            extra_fields={
                                "frames_processed": self.frames_processed,
                                "frame_count_in_engine": getattr(self.engine, "_frame_count", "unknown"),
                            },
                        )

                self.frames_processed += 1
                self._queue.task_done()

            except asyncio.CancelledError:
                logger.info("STT consumer processing loop cancelled")
                break
            except Exception as e:
                logger.error(
                    "Error processing frame in STT consumer",
                    extra_fields={"error": str(e)},
                    exc_info=True,
                )

        logger.debug("STT consumer processing loop ended")

    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running
