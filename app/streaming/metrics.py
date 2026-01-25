"""Latency profiling and backpressure metrics for streaming pipeline."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Backpressure threshold (percentage of max queue size)
BACKPRESSURE_THRESHOLD_PERCENT = 0.8  # 80% of max size


@dataclass
class FrameMetrics:
    """Metrics for a single audio frame."""

    enqueue_time: float
    dequeue_time: Optional[float] = None
    dispatch_time: Optional[float] = None

    def get_latency_ms(self) -> Optional[float]:
        """Calculate total latency from enqueue to dispatch in milliseconds.

        Returns:
            Latency in milliseconds or None if not fully processed
        """
        if self.enqueue_time and self.dispatch_time:
            return (self.dispatch_time - self.enqueue_time) * 1000.0
        return None


class StreamingMetrics:
    """Singleton thread-safe metrics collector for streaming pipeline.

    Tracks latency, queue depth, and backpressure indicators.
    Uses lock-free operations where possible for performance.

    Attributes:
        current_latency_ms: Current latency in milliseconds
        max_latency_ms: Maximum latency observed
        queue_depth: Current queue depth
        dropped_frames: Count of dropped frames
        _frame_metrics: Dictionary mapping frame IDs to metrics
        _max_queue_depth: Maximum queue depth observed
        _latencies: Recent latency measurements (for avg/max calculation)
        _total_latency_ms: Sum of all latencies (for average calculation)
        _latency_count: Number of latency measurements
    """

    _instance: Optional["StreamingMetrics"] = None

    def __new__(cls, max_latency_samples: int = 1000):
        """Singleton pattern - return existing instance if available."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "StreamingMetrics":
        """Get the singleton instance.

        Returns:
            StreamingMetrics singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, max_latency_samples: int = 1000):
        """Initialize metrics collector (only once due to singleton).

        Args:
            max_latency_samples: Maximum number of latency samples to keep
        """
        if self._initialized:
            return

        self.current_latency_ms = 0.0
        self.max_latency_ms = 0.0
        self.queue_depth = 0
        self.dropped_frames = 0

        self._frame_metrics: dict[int, FrameMetrics] = {}
        self._max_queue_depth = 0
        self._latencies: deque[float] = deque(maxlen=max_latency_samples)
        self._total_latency_ms = 0.0
        self._latency_count = 0
        self._frame_id_counter = 0
        self._initialized = True

    def record_enqueue(self, queue_depth: int, max_size: int) -> int:
        """Record frame enqueue event.

        Args:
            queue_depth: Current queue depth
            max_size: Maximum queue size

        Returns:
            Frame ID for tracking
        """
        frame_id = self._frame_id_counter
        self._frame_id_counter += 1

        # Update queue depth tracking (lock-free, single writer)
        self.queue_depth = queue_depth
        if queue_depth > self._max_queue_depth:
            self._max_queue_depth = queue_depth

        # Record enqueue timestamp
        self._frame_metrics[frame_id] = FrameMetrics(enqueue_time=time.time())

        # Check backpressure threshold
        if queue_depth >= max_size * BACKPRESSURE_THRESHOLD_PERCENT:
            logger.warning(
                "Backpressure detected - queue approaching capacity",
                extra_fields={
                    "queue_depth": queue_depth,
                    "max_size": max_size,
                    "threshold_percent": BACKPRESSURE_THRESHOLD_PERCENT * 100,
                },
            )

        return frame_id

    def record_drop(self, queue_depth: int, max_size: int) -> None:
        """Record frame drop event.

        Args:
            queue_depth: Current queue depth
            max_size: Maximum queue size
        """
        self.dropped_frames += 1

        logger.warning(
            "Frame dropped due to queue overflow",
            extra_fields={
                "queue_depth": queue_depth,
                "max_size": max_size,
                "total_dropped": self.dropped_frames,
            },
        )

    def record_dequeue(self, frame_id: int, queue_depth: int) -> None:
        """Record frame dequeue event.

        Args:
            frame_id: Frame ID from record_enqueue
            queue_depth: Current queue depth after dequeue
        """
        if frame_id in self._frame_metrics:
            self._frame_metrics[frame_id].dequeue_time = time.time()
        
        # Update current queue depth
        self.queue_depth = queue_depth

    def record_dispatch(self, frame_id: int) -> None:
        """Record frame dispatch event and calculate latency.

        Args:
            frame_id: Frame ID from record_enqueue
        """
        if frame_id not in self._frame_metrics:
            return

        metrics = self._frame_metrics[frame_id]
        metrics.dispatch_time = time.time()

        # Calculate and record latency
        latency_ms = metrics.get_latency_ms()
        if latency_ms is not None:
            self._latencies.append(latency_ms)
            self._total_latency_ms += latency_ms
            self._latency_count += 1

            # Update current and max latency
            self.current_latency_ms = latency_ms
            if latency_ms > self.max_latency_ms:
                self.max_latency_ms = latency_ms

        # Clean up old metrics (keep only recent ones)
        if len(self._frame_metrics) > 1000:
            # Remove oldest 500 entries
            oldest_ids = sorted(self._frame_metrics.keys())[:500]
            for old_id in oldest_ids:
                del self._frame_metrics[old_id]

    def get_average_latency_ms(self) -> float:
        """Get average dispatch latency in milliseconds.

        Returns:
            Average latency in milliseconds, 0.0 if no measurements
        """
        if self._latency_count == 0:
            return 0.0
        return self._total_latency_ms / self._latency_count

    def get_max_latency_ms(self) -> float:
        """Get maximum dispatch latency in milliseconds.

        Returns:
            Maximum latency in milliseconds
        """
        return self.max_latency_ms

    def get_current_latency_ms(self) -> float:
        """Get most recent latency measurement.

        Returns:
            Most recent latency in milliseconds
        """
        return self.current_latency_ms

    def get_stats(self) -> dict:
        """Get comprehensive metrics statistics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "current_latency_ms": round(self.current_latency_ms, 2),
            "average_latency_ms": round(self.get_average_latency_ms(), 2),
            "max_latency_ms": round(self.max_latency_ms, 2),
            "dropped_frames": self.dropped_frames,
            "queue_depth": self.queue_depth,
            "max_queue_depth": self._max_queue_depth,
            "latency_samples": len(self._latencies),
        }

    def reset(self) -> None:
        """Reset all metrics (for testing or cleanup)."""
        self._frame_metrics.clear()
        self._max_queue_depth = 0
        self.queue_depth = 0
        self.dropped_frames = 0
        self._latencies.clear()
        self.max_latency_ms = 0.0
        self.current_latency_ms = 0.0
        self._total_latency_ms = 0.0
        self._latency_count = 0
        self._frame_id_counter = 0


# Singleton instance - use this to access metrics
streaming_metrics = StreamingMetrics()
