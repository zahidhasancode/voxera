"""Non-blocking async audio pipeline with fan-out to multiple consumers."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AudioChunk:
    """Audio chunk with metadata."""

    data: bytes
    call_id: str
    timestamp: datetime
    sequence: int


class AudioConsumer(ABC):
    """Abstract base class for audio consumers."""

    def __init__(self, name: str, max_queue_size: int = 100):
        """Initialize audio consumer.

        Args:
            name: Consumer name for logging
            max_queue_size: Maximum queue size for backpressure handling
        """
        self.name = name
        self.max_queue_size = max_queue_size
        self._queue: asyncio.Queue[Optional[AudioChunk]] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.chunks_processed = 0
        self.chunks_dropped = 0

    async def start(self) -> None:
        """Start consumer processing."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.debug(f"Audio consumer '{self.name}' started")

    async def stop(self) -> None:
        """Stop consumer processing."""
        if not self._running:
            return

        self._running = False
        # Signal shutdown with None
        await self._queue.put(None)

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Consumer '{self.name}' did not stop gracefully")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.debug(
            f"Audio consumer '{self.name}' stopped",
            extra_fields={
                "chunks_processed": self.chunks_processed,
                "chunks_dropped": self.chunks_dropped,
            },
        )

    async def put_chunk(self, chunk: AudioChunk) -> bool:
        """Non-blocking put chunk into consumer queue.

        Args:
            chunk: Audio chunk to process

        Returns:
            True if chunk was queued, False if dropped due to backpressure
        """
        try:
            self._queue.put_nowait(chunk)
            return True
        except asyncio.QueueFull:
            self.chunks_dropped += 1
            logger.warning(
                f"Consumer '{self.name}' queue full, dropping chunk",
                extra_fields={"call_id": chunk.call_id},
            )
            return False

    async def _process_loop(self) -> None:
        """Internal processing loop."""
        while self._running:
            try:
                chunk = await self._queue.get()
                if chunk is None:  # Shutdown signal
                    break

                await self.process_chunk(chunk)
                self.chunks_processed += 1
                self._queue.task_done()
            except Exception as e:
                logger.exception(
                    f"Error processing chunk in consumer '{self.name}'",
                    extra_fields={"error": str(e)},
                )

    @abstractmethod
    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Process a single audio chunk.

        Args:
            chunk: Audio chunk to process
        """
        pass

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running


class AudioPipeline:
    """Non-blocking audio pipeline with fan-out to multiple consumers."""

    def __init__(self, call_id: str):
        """Initialize audio pipeline.

        Args:
            call_id: Call session ID
        """
        self.call_id = call_id
        self._consumers: list[AudioConsumer] = []
        self._running = False
        self._sequence = 0

    def add_consumer(self, consumer: AudioConsumer) -> None:
        """Add a consumer to the pipeline.

        Args:
            consumer: Audio consumer to add
        """
        if consumer in self._consumers:
            return

        self._consumers.append(consumer)
        logger.debug(
            f"Consumer '{consumer.name}' added to pipeline",
            extra_fields={"call_id": self.call_id},
        )

    def remove_consumer(self, consumer: AudioConsumer) -> None:
        """Remove a consumer from the pipeline.

        Args:
            consumer: Audio consumer to remove
        """
        if consumer in self._consumers:
            self._consumers.remove(consumer)
            logger.debug(
                f"Consumer '{consumer.name}' removed from pipeline",
                extra_fields={"call_id": self.call_id},
            )

    async def start(self) -> None:
        """Start pipeline and all consumers."""
        if self._running:
            return

        self._running = True
        # Start all consumers
        for consumer in self._consumers:
            await consumer.start()

        logger.info(
            f"Audio pipeline started with {len(self._consumers)} consumers",
            extra_fields={"call_id": self.call_id},
        )

    async def stop(self) -> None:
        """Stop pipeline and all consumers."""
        if not self._running:
            return

        self._running = False

        # Stop all consumers
        stop_tasks = [consumer.stop() for consumer in self._consumers]
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info(
            "Audio pipeline stopped",
            extra_fields={
                "call_id": self.call_id,
                "consumers": len(self._consumers),
            },
        )

    async def _put_chunk_safe(self, consumer: AudioConsumer, chunk: AudioChunk) -> None:
        """Safely put chunk to consumer (wrapper for error handling).

        Args:
            consumer: Consumer to send chunk to
            chunk: Audio chunk
        """
        try:
            await consumer.put_chunk(chunk)
        except Exception as e:
            logger.error(
                f"Error putting chunk to consumer '{consumer.name}'",
                extra_fields={
                    "call_id": self.call_id,
                    "error": str(e),
                },
            )

    async def ingest_chunk(self, audio_data: bytes) -> None:
        """Ingest audio chunk and fan-out to all consumers.

        This method never blocks - if a consumer's queue is full,
        the chunk is dropped for that consumer only.

        Args:
            audio_data: PCM audio bytes
        """
        if not self._running:
            logger.warning(
                "Pipeline not running, ignoring chunk",
                extra_fields={"call_id": self.call_id},
            )
            return

        # Create audio chunk
        self._sequence += 1
        chunk = AudioChunk(
            data=audio_data,
            call_id=self.call_id,
            timestamp=datetime.now(timezone.utc),
            sequence=self._sequence,
        )

        # Fan-out to all consumers (non-blocking)
        # Use asyncio.create_task to ensure we never block
        for consumer in self._consumers:
            if consumer.is_running:
                # Schedule put_chunk without waiting - truly non-blocking
                asyncio.create_task(self._put_chunk_safe(consumer, chunk))

    @property
    def consumer_count(self) -> int:
        """Get number of active consumers."""
        return len(self._consumers)

    @property
    def is_running(self) -> bool:
        """Check if pipeline is running."""
        return self._running


# Example consumer implementations for testing and future use


class NullConsumer(AudioConsumer):
    """Null consumer that discards chunks (for testing)."""

    def __init__(self, name: str = "null", max_queue_size: int = 100):
        """Initialize null consumer."""
        super().__init__(name, max_queue_size)

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Discard chunk."""
        pass


class MetricsConsumer(AudioConsumer):
    """Consumer that tracks audio metrics."""

    def __init__(self, name: str = "metrics", max_queue_size: int = 100):
        """Initialize metrics consumer."""
        super().__init__(name, max_queue_size)
        self.total_bytes = 0
        self.chunk_count = 0

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Process chunk for metrics."""
        self.total_bytes += len(chunk.data)
        self.chunk_count += 1

    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            "total_bytes": self.total_bytes,
            "chunk_count": self.chunk_count,
            "avg_chunk_size": self.total_bytes / self.chunk_count
            if self.chunk_count > 0
            else 0,
        }


class RecorderConsumer(AudioConsumer):
    """Consumer that records audio (placeholder for future implementation)."""

    def __init__(self, name: str = "recorder", max_queue_size: int = 100):
        """Initialize recorder consumer."""
        super().__init__(name, max_queue_size)
        self.recorded_chunks: list[AudioChunk] = []

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Record chunk."""
        # Placeholder: In future, this would write to file/storage
        self.recorded_chunks.append(chunk)

    def get_recorded_data(self) -> bytes:
        """Get all recorded audio data."""
        return b"".join(chunk.data for chunk in self.recorded_chunks)
