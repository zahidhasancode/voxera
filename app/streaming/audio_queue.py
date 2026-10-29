"""Bounded async queue for audio frames with drop-oldest policy."""

import asyncio
from collections import deque
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class FrameWithId:
    """Frame with tracking ID for metrics."""

    def __init__(self, frame: bytes, frame_id: int):
        """Initialize frame with ID.

        Args:
            frame: Audio frame bytes
            frame_id: Unique frame ID for metrics tracking
        """
        self.frame = frame
        self.frame_id = frame_id


class AudioFrameQueue:
    """Bounded async queue for audio frames with drop-oldest policy.

    This queue maintains a fixed maximum size. When full, the oldest frame
    is dropped to make room for new frames, preventing unbounded growth
    and ensuring low latency.

    Attributes:
        max_size: Maximum number of frames in queue
        _queue: Internal deque for frame storage
        _lock: Async lock for thread-safe operations
        frames_dropped: Counter for dropped frames
        frames_enqueued: Counter for enqueued frames
    """

    def __init__(self, max_size: int = 50, metrics=None):
        """Initialize audio frame queue.

        Args:
            max_size: Maximum number of frames (default: 50)
            metrics: Optional StreamingMetrics instance for instrumentation
        """
        if max_size < 1:
            raise ValueError("max_size must be at least 1")

        self.max_size = max_size
        self._queue: deque[FrameWithId] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        # Set while at least one frame is waiting, so consumers can sleep until a frame arrives.
        self._not_empty = asyncio.Event()
        self.frames_dropped = 0
        self.frames_enqueued = 0
        self._metrics = metrics

    async def enqueue(self, frame: bytes) -> bool:
        """Non-blocking enqueue of audio frame.

        If queue is full, drops oldest frame and adds new one.

        Args:
            frame: Audio frame bytes (20ms PCM16)

        Returns:
            True if frame was enqueued, False if dropped (should not happen with drop-oldest)
        """
        async with self._lock:
            queue_depth = len(self._queue)
            was_full = queue_depth >= self.max_size

            # Record metrics before enqueue
            frame_id = None
            if self._metrics:
                frame_id = self._metrics.record_enqueue(queue_depth, self.max_size)

            if was_full:
                # Record drop of oldest frame
                if self._queue and self._metrics:
                    self._metrics.record_drop(queue_depth, self.max_size)

                # Drop oldest frame (deque with maxlen does this automatically)
                self.frames_dropped += 1
                logger.debug(
                    "Audio frame queue full, dropping oldest frame",
                    extra_fields={
                        "queue_depth": queue_depth,
                        "max_size": self.max_size,
                        "total_dropped": self.frames_dropped,
                    },
                )

            # Add new frame (deque with maxlen automatically drops oldest if full)
            frame_with_id = FrameWithId(frame, frame_id) if frame_id is not None else FrameWithId(frame, -1)
            self._queue.append(frame_with_id)
            self.frames_enqueued += 1
            self._not_empty.set()

            return True

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[FrameWithId]:
        """Dequeue audio frame with optional timeout.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            FrameWithId object or None if timeout/empty
        """
        async with self._lock:
            if len(self._queue) > 0:
                frame_with_id = self._queue.popleft()
                # Record dequeue in metrics
                queue_depth_after = len(self._queue)
                if self._metrics and frame_with_id.frame_id >= 0:
                    self._metrics.record_dequeue(frame_with_id.frame_id, queue_depth_after)
                if not self._queue:
                    self._not_empty.clear()
                return frame_with_id
            self._not_empty.clear()
            return None

    async def wait_for_frame(self, timeout: Optional[float] = None) -> bool:
        """Sleep until a frame is waiting (or the timeout passes). Returns True if one is."""
        if self._queue:
            return True
        try:
            await asyncio.wait_for(self._not_empty.wait(), timeout)
        except asyncio.TimeoutError:
            return False
        return True

    async def dequeue_blocking(self) -> FrameWithId:
        """Blocking dequeue - waits until frame is available.

        Returns:
            FrameWithId object
        """
        while True:
            frame = await self.dequeue()
            if frame is not None:
                return frame
            await self.wait_for_frame()

    def size(self) -> int:
        """Get current queue size.

        Returns:
            Number of frames in queue
        """
        return len(self._queue)

    def is_empty(self) -> bool:
        """Check if queue is empty.

        Returns:
            True if empty, False otherwise
        """
        return len(self._queue) == 0

    def is_full(self) -> bool:
        """Check if queue is full.

        Returns:
            True if full, False otherwise
        """
        return len(self._queue) >= self.max_size

    def get_stats(self) -> dict:
        """Get queue statistics.

        Returns:
            Dictionary with queue stats
        """
        return {
            "queue_depth": len(self._queue),
            "max_size": self.max_size,
            "frames_enqueued": self.frames_enqueued,
            "frames_dropped": self.frames_dropped,
            "is_full": self.is_full(),
        }

    def clear(self) -> None:
        """Clear all frames from queue."""
        self._queue.clear()
        self._not_empty.clear()
