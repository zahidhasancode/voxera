"""Streaming dispatcher: forwards inbound audio frames to their consumers."""

import asyncio
import time
from typing import Awaitable, Callable, Optional

from app.core.logger import get_logger

from app.streaming.audio_queue import AudioFrameQueue
from app.streaming.metrics import StreamingMetrics

logger = get_logger(__name__)

# How long to wait before looking again when the queue is empty
IDLE_POLL_SEC = 0.002

# Frame interval in seconds (20ms)
FRAME_INTERVAL_MS = 20
FRAME_INTERVAL_SEC = FRAME_INTERVAL_MS / 1000.0


class StreamingDispatcher:
    """Dispatches audio frames in arrival order, without adding delay.

    This dispatcher maintains a constant frame rate by pulling frames
    from the queue every 20ms and passing them to a callback function.
    It ensures no blocking and maintains real-time performance.

    Attributes:
        queue: AudioFrameQueue to pull frames from
        callback: Async callback function to process frames
        _running: Flag indicating if dispatcher is running
        _task: Background task for frame dispatch
        frames_dispatched: Counter for dispatched frames
        _last_dispatch_time: Timestamp of last frame dispatch
    """

    def __init__(
        self,
        queue: AudioFrameQueue,
        callback: Callable[[bytes], Awaitable[None]],
        metrics: Optional[StreamingMetrics] = None,
    ):
        """Initialize streaming dispatcher.

        Args:
            queue: AudioFrameQueue to pull frames from
            callback: Async callback function(frame: bytes) -> None
            metrics: Optional StreamingMetrics instance for instrumentation
        """
        self.queue = queue
        self.callback = callback
        self._metrics = metrics
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.frames_dispatched = 0
        self._last_dispatch_time: Optional[float] = None
        self._stt_consumer: Optional[object] = None

    async def start(self) -> None:
        """Start the dispatcher.

        Creates a background task that pulls frames every 20ms.
        """
        if self._running:
            logger.warning("Dispatcher already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())
        logger.info(
            "Streaming dispatcher started",
            extra_fields={
                "frame_interval_ms": FRAME_INTERVAL_MS,
            },
        )

    async def stop(self) -> None:
        """Stop the dispatcher.

        Stops the background task and waits for it to complete.
        """
        if not self._running:
            return

        self._running = False

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=1.0)
            except asyncio.TimeoutError:
                logger.warning("Dispatcher did not stop gracefully, cancelling")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info(
            "Streaming dispatcher stopped",
            extra_fields={
                "frames_dispatched": self.frames_dispatched,
            },
        )

    async def _dispatch_loop(self) -> None:
        """Main dispatch loop: forward every queued frame as soon as it arrives.

        Frames arrive from the client at their own real-time cadence (one per
        20 ms), so the dispatcher must not add a timer of its own: a loop that
        takes one frame per 20 ms tick can never catch up after the smallest
        delay, and the queue slowly fills until it adds its full length (about
        one second) to every turn and starts dropping audio. The loop drains
        whatever is waiting and only idles when the queue is empty.
        """
        while self._running:
            frame_with_id = await self.queue.dequeue()

            if frame_with_id is None:
                await asyncio.sleep(IDLE_POLL_SEC)
                continue

            try:
                await self.callback(frame_with_id.frame)
                self.frames_dispatched += 1

                # Record dispatch in metrics
                if self._metrics and frame_with_id.frame_id >= 0:
                    self._metrics.record_dispatch(frame_with_id.frame_id)

                # Hand the frame to the STT consumer (non-blocking put; keeps frame order)
                if self._stt_consumer and self._stt_consumer.is_running():
                    await self._stt_consumer.process_frame(frame_with_id.frame)

            except Exception as e:
                logger.error(
                    "Error in frame callback",
                    extra_fields={"error": str(e)},
                    exc_info=True,
                )

            self._last_dispatch_time = time.time()
            # Let the WebSocket receive loop run between frames.
            await asyncio.sleep(0)

    def register_stt_consumer(self, stt_consumer: object) -> None:
        """Register STT consumer to receive audio frames.

        Args:
            stt_consumer: STTConsumer instance
        """
        self._stt_consumer = stt_consumer
        logger.debug("STT consumer registered with dispatcher")

    def is_running(self) -> bool:
        """Check if dispatcher is running.

        Returns:
            True if running, False otherwise
        """
        return self._running

    def get_stats(self) -> dict:
        """Get dispatcher statistics.

        Returns:
            Dictionary with dispatcher stats
        """
        stats = {
            "is_running": self._running,
            "frames_dispatched": self.frames_dispatched,
            "queue_stats": self.queue.get_stats(),
        }

        # Add metrics if available
        if self._metrics:
            metrics_stats = self._metrics.get_stats()
            stats["metrics"] = metrics_stats

        return stats
