"""Unit tests for audio pipeline throughput and concurrency."""

import asyncio
import time
from datetime import datetime

import pytest

from app.services.audio_pipeline import (
    AudioChunk,
    AudioConsumer,
    AudioPipeline,
    MetricsConsumer,
    NullConsumer,
)


class SlowConsumer(AudioConsumer):
    """Slow consumer for testing backpressure."""

    def __init__(self, name: str, delay: float = 0.001, max_queue_size: int = 10):
        """Initialize slow consumer.

        Args:
            name: Consumer name
            delay: Processing delay in seconds
            max_queue_size: Maximum queue size
        """
        super().__init__(name, max_queue_size)
        self.delay = delay
        self.processed_chunks = []

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Process chunk with delay."""
        await asyncio.sleep(self.delay)
        self.processed_chunks.append(chunk)


class CountingConsumer(AudioConsumer):
    """Consumer that counts chunks."""

    def __init__(self, name: str, max_queue_size: int = 100):
        """Initialize counting consumer."""
        super().__init__(name, max_queue_size)
        self.count = 0

    async def process_chunk(self, chunk: AudioChunk) -> None:
        """Count chunk."""
        self.count += 1


@pytest.fixture
async def pipeline():
    """Create a test pipeline."""
    pipeline = AudioPipeline(call_id="test-call-123")
    await pipeline.start()
    yield pipeline
    await pipeline.stop()


@pytest.mark.asyncio
async def test_pipeline_throughput(pipeline):
    """Test pipeline can handle high throughput."""
    # Add a null consumer that processes quickly
    consumer = NullConsumer(name="test", max_queue_size=1000)
    pipeline.add_consumer(consumer)
    await consumer.start()

    # Send chunks as fast as possible
    num_chunks = 10000
    chunk_size = 1600  # ~20ms of PCM at 8kHz
    chunk_data = b"0" * chunk_size

    start_time = time.time()

    for _ in range(num_chunks):
        await pipeline.ingest_chunk(chunk_data)

    # Wait for processing to complete
    await asyncio.sleep(0.1)

    elapsed = time.time() - start_time
    throughput = num_chunks / elapsed

    # Should process at least 1000 chunks/second
    assert throughput > 1000, f"Throughput too low: {throughput} chunks/sec"

    await consumer.stop()


@pytest.mark.asyncio
async def test_pipeline_fanout(pipeline):
    """Test pipeline fans out to multiple consumers."""
    # Create multiple consumers
    consumers = [CountingConsumer(name=f"consumer-{i}") for i in range(5)]
    for consumer in consumers:
        pipeline.add_consumer(consumer)
        await consumer.start()

    # Send chunks
    num_chunks = 100
    chunk_data = b"test" * 100

    for _ in range(num_chunks):
        await pipeline.ingest_chunk(chunk_data)

    # Wait for processing
    await asyncio.sleep(0.5)

    # All consumers should have received all chunks
    for consumer in consumers:
        assert consumer.count == num_chunks, f"Consumer {consumer.name} missed chunks"

    # Stop consumers
    for consumer in consumers:
        await consumer.stop()


@pytest.mark.asyncio
async def test_backpressure_handling(pipeline):
    """Test backpressure is handled gracefully without blocking."""
    # Create a slow consumer with small queue
    slow_consumer = SlowConsumer(name="slow", delay=0.01, max_queue_size=5)
    pipeline.add_consumer(slow_consumer)
    await slow_consumer.start()

    # Send chunks faster than consumer can process
    num_chunks = 100
    chunk_data = b"test" * 100

    start_time = time.time()
    # This should not block even when queue fills up
    for i in range(num_chunks):
        await pipeline.ingest_chunk(chunk_data)

    ingest_time = time.time() - start_time

    # Ingestion should be fast (non-blocking)
    assert ingest_time < 0.1, "Ingestion blocked on backpressure"

    # Wait for processing
    await asyncio.sleep(2.0)

    # Some chunks should be processed, some may be dropped
    assert slow_consumer.chunks_processed > 0, "No chunks were processed"
    assert (
        slow_consumer.chunks_dropped > 0
    ), "Expected some chunks to be dropped due to backpressure"

    await slow_consumer.stop()


@pytest.mark.asyncio
async def test_concurrent_pipelines():
    """Test multiple pipelines can run concurrently."""
    num_pipelines = 10
    pipelines = []
    consumers_per_pipeline = 3

    # Create multiple pipelines
    for i in range(num_pipelines):
        pipeline = AudioPipeline(call_id=f"call-{i}")
        for j in range(consumers_per_pipeline):
            consumer = CountingConsumer(name=f"call-{i}-consumer-{j}")
            pipeline.add_consumer(consumer)
            await consumer.start()
        await pipeline.start()
        pipelines.append((pipeline, [consumer for consumer in pipeline._consumers]))

    # Send chunks to all pipelines concurrently
    num_chunks = 50
    chunk_data = b"test" * 100

    async def send_to_pipeline(pipeline_tuple):
        """Send chunks to a pipeline."""
        pipeline, _ = pipeline_tuple
        for _ in range(num_chunks):
            await pipeline.ingest_chunk(chunk_data)

    # Send concurrently
    await asyncio.gather(*[send_to_pipeline(p) for p in pipelines])

    # Wait for processing
    await asyncio.sleep(1.0)

    # Verify all pipelines processed chunks
    for pipeline, consumers in pipelines:
        for consumer in consumers:
            assert consumer.count == num_chunks, f"Consumer missed chunks"

    # Cleanup
    for pipeline, _ in pipelines:
        await pipeline.stop()


@pytest.mark.asyncio
async def test_consumer_start_stop(pipeline):
    """Test consumers can be started and stopped safely."""
    consumer1 = CountingConsumer(name="consumer1")
    consumer2 = CountingConsumer(name="consumer2")

    pipeline.add_consumer(consumer1)
    pipeline.add_consumer(consumer2)

    await pipeline.start()

    # Send some chunks
    for _ in range(10):
        await pipeline.ingest_chunk(b"test")

    await asyncio.sleep(0.1)

    assert consumer1.count == 10
    assert consumer2.count == 10

    # Remove one consumer
    pipeline.remove_consumer(consumer1)
    await consumer1.stop()

    # Send more chunks - only consumer2 should receive them
    for _ in range(10):
        await pipeline.ingest_chunk(b"test")

    await asyncio.sleep(0.1)

    assert consumer1.count == 10  # Unchanged
    assert consumer2.count == 20  # Received new chunks

    await pipeline.stop()


@pytest.mark.asyncio
async def test_metrics_consumer():
    """Test metrics consumer tracks statistics correctly."""
    pipeline = AudioPipeline(call_id="metrics-test")
    consumer = MetricsConsumer(name="metrics")
    pipeline.add_consumer(consumer)

    await pipeline.start()

    # Send chunks of varying sizes
    chunks = [b"a" * 100, b"b" * 200, b"c" * 150]

    for chunk_data in chunks:
        await pipeline.ingest_chunk(chunk_data)

    await asyncio.sleep(0.2)

    metrics = consumer.get_metrics()

    assert metrics["chunk_count"] == 3
    assert metrics["total_bytes"] == 450  # 100 + 200 + 150
    assert metrics["avg_chunk_size"] == 150.0

    await pipeline.stop()


@pytest.mark.asyncio
async def test_pipeline_never_blocks_ingestion(pipeline):
    """Test that ingestion never blocks even with slow consumers."""
    # Create multiple slow consumers
    consumers = [
        SlowConsumer(name=f"slow-{i}", delay=0.05, max_queue_size=2)
        for i in range(5)
    ]

    for consumer in consumers:
        pipeline.add_consumer(consumer)
        await consumer.start()

    # Send chunks rapidly
    num_chunks = 1000
    chunk_data = b"test" * 100

    start_time = time.time()
    for _ in range(num_chunks):
        await pipeline.ingest_chunk(chunk_data)
    ingest_time = time.time() - start_time

    # Ingestion should be very fast (non-blocking)
    # Even with 1000 chunks and slow consumers, should take < 0.5 seconds
    assert ingest_time < 0.5, f"Ingestion blocked: took {ingest_time}s"

    # Wait for processing
    await asyncio.sleep(3.0)

    # Verify some chunks were processed
    total_processed = sum(c.chunks_processed for c in consumers)
    assert total_processed > 0, "Some chunks should have been processed"

    for consumer in consumers:
        await consumer.stop()


@pytest.mark.asyncio
async def test_chunk_sequence_numbers(pipeline):
    """Test that chunks maintain sequence numbers."""
    consumer = CountingConsumer(name="seq-test")
    pipeline.add_consumer(consumer)

    # Store chunks to check sequence
    received_chunks = []

    class SeqCheckConsumer(AudioConsumer):
        async def process_chunk(self, chunk: AudioChunk):
            received_chunks.append(chunk)

    seq_consumer = SeqCheckConsumer(name="seq-check")
    pipeline.add_consumer(seq_consumer)

    await pipeline.start()

    # Send chunks
    for i in range(10):
        await pipeline.ingest_chunk(f"chunk-{i}".encode())

    await asyncio.sleep(0.2)

    # Verify sequence numbers are sequential
    sequences = [chunk.sequence for chunk in received_chunks]
    assert sequences == list(range(1, 11)), "Sequence numbers should be sequential"

    await pipeline.stop()
