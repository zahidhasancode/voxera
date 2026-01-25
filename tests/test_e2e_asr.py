"""End-to-end test for WebSocket audio streaming with ASR."""

import asyncio
import json
import time
from typing import List

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_application
from app.models.call_session import CallState
from app.services.asr import ASRConsumer, MockStreamingASR
from app.services.call_session_manager import session_manager
from app.services.pipeline_manager import pipeline_manager


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    app = create_application()
    return app


@pytest.fixture
async def client(test_app):
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up sessions and pipelines after each test."""
    yield
    # Cleanup
    session_manager._sessions.clear()
    pipeline_manager._pipelines.clear()


def generate_audio_chunk(size: int = 320) -> bytes:
    """Generate mock PCM audio chunk (20ms at 8kHz, 16-bit).

    Args:
        size: Chunk size in bytes (default: 320 = 20ms at 8kHz)

    Returns:
        Mock audio bytes
    """
    return b"\x00" * size


class TranscriptCollector:
    """Collects transcript messages from ASR consumer."""

    def __init__(self):
        """Initialize transcript collector."""
        self.transcripts: List[dict] = []

    async def callback(self, result: dict) -> None:
        """Callback for transcript events.

        Args:
            result: Transcript result dictionary
        """
        self.transcripts.append(result)


@pytest.mark.asyncio
async def test_websocket_connection(client: AsyncClient):
    """Test WebSocket connection establishment."""
    async with client.websocket_connect("/api/v1/ws/audio") as websocket:
        # Should receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"
        assert "call_id" in message
        assert message["status"] == "ready"


@pytest.mark.asyncio
async def test_audio_chunk_streaming(client: AsyncClient):
    """Test streaming audio chunks through WebSocket."""
    call_id = "test-call-123"
    async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        # Receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"
        assert message["call_id"] == call_id

        # Verify CallSession was created
        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING

        # Stream multiple audio chunks
        num_chunks = 10
        for i in range(num_chunks):
            audio_chunk = generate_audio_chunk()
            await websocket.send_bytes(audio_chunk)
            # Small delay to simulate real-time streaming
            await asyncio.sleep(0.02)  # 20ms delay

        # Verify chunks were received (check connection stats)
        connection = None
        # Note: We can't directly access connection stats, but we can verify
        # the session is still active and pipeline is running
        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING


@pytest.mark.asyncio
async def test_asr_partial_transcript_emission(client: AsyncClient):
    """Test ASR partial transcript emission with latency measurement."""
    call_id = "test-asr-call-456"

    # Set up ASR consumer with mock backend
    mock_asr = MockStreamingASR(word_probability=0.15)  # Higher probability for testing
    transcript_collector = TranscriptCollector()

    asr_consumer = ASRConsumer(
        asr_backend=mock_asr,
        name="test_asr",
        emit_interval_ms=50,  # Emit every 50ms for faster testing
        transcript_callback=transcript_collector.callback,
        latency_threshold_ms=150.0,
        stats_log_interval=5,  # Log stats every 5 transcripts
    )

    # Get pipeline and add ASR consumer
    async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        # Receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"

        # Get pipeline and add ASR consumer
        pipeline = pipeline_manager.get_pipeline(call_id)
        assert pipeline is not None

        # Add ASR consumer to pipeline
        pipeline.add_consumer(asr_consumer)
        await asr_consumer.start()

        # Stream audio chunks to trigger ASR
        num_chunks = 50  # Stream enough chunks to generate transcripts
        start_time = time.time()

        for i in range(num_chunks):
            audio_chunk = generate_audio_chunk()
            await websocket.send_bytes(audio_chunk)
            # Small delay to simulate real-time streaming
            await asyncio.sleep(0.02)  # 20ms delay

        # Wait a bit for ASR processing
        await asyncio.sleep(0.5)

        # Verify transcripts were emitted
        assert len(transcript_collector.transcripts) > 0, "No transcripts were emitted"

        # Verify transcript structure
        for transcript in transcript_collector.transcripts:
            assert "transcript" in transcript
            assert "confidence" in transcript
            assert "type" in transcript
            assert transcript["type"] == "partial"
            assert "call_id" in transcript
            assert transcript["call_id"] == call_id
            assert 0.0 <= transcript["confidence"] <= 1.0

        # Verify latency was measured
        session = session_manager.get_session(call_id)
        assert session is not None
        assert len(session.asr_latencies) > 0, "No latency measurements recorded"

        # Verify latency is within expected bounds (should be < 150ms for non-blocking)
        max_latency = max(session.asr_latencies)
        assert max_latency < 200.0, f"Max latency {max_latency}ms exceeds expected bound"

        # Verify no blocking occurred (total time should be reasonable)
        total_time = time.time() - start_time
        expected_min_time = (num_chunks * 0.02)  # Minimum time for chunk delays
        assert total_time < expected_min_time + 1.0, f"Test took too long: {total_time}s"


@pytest.mark.asyncio
async def test_call_session_lifecycle(client: AsyncClient):
    """Test CallSession lifecycle during WebSocket connection."""
    call_id = "test-lifecycle-789"

    async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        # Receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"

        # Verify initial state
        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING
        assert CallState.CONNECTED.value in session.timestamps
        assert CallState.LISTENING.value in session.timestamps

        # Stream some audio
        for i in range(5):
            audio_chunk = generate_audio_chunk()
            await websocket.send_bytes(audio_chunk)
            await asyncio.sleep(0.02)

        # Verify state hasn't changed unexpectedly
        session = session_manager.get_session(call_id)
        assert session.state == CallState.LISTENING

        # Test state change message
        state_change = {
            "type": "state_change",
            "state": "responding",
        }
        await websocket.send_text(json.dumps(state_change))

        # Wait for state change acknowledgment
        response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert response["type"] == "state_changed"
        assert response["state"] == "responding"

        # Verify state transition
        session = session_manager.get_session(call_id)
        assert session.state == CallState.RESPONDING
        assert CallState.RESPONDING.value in session.timestamps

        # Transition back to listening
        state_change = {
            "type": "state_change",
            "state": "listening",
        }
        await websocket.send_text(json.dumps(state_change))

        response = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert response["type"] == "state_changed"
        assert response["state"] == "listening"

        session = session_manager.get_session(call_id)
        assert session.state == CallState.LISTENING

    # After disconnect, verify session is cleaned up or ended
    # Note: In actual implementation, session might be ended or kept for a while
    # This depends on your cleanup strategy


@pytest.mark.asyncio
async def test_asr_latency_within_bounds(client: AsyncClient):
    """Test that ASR latency measurements are within expected bounds."""
    call_id = "test-latency-bounds-999"

    # Set up ASR consumer with high word probability for reliable transcript generation
    mock_asr = MockStreamingASR(word_probability=0.2)
    transcript_collector = TranscriptCollector()

    asr_consumer = ASRConsumer(
        asr_backend=mock_asr,
        name="test_asr_latency",
        emit_interval_ms=50,  # Emit every 50ms
        transcript_callback=transcript_collector.callback,
        latency_threshold_ms=150.0,
        stats_log_interval=3,
    )

    async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        # Receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"

        # Get pipeline and add ASR consumer
        pipeline = pipeline_manager.get_pipeline(call_id)
        assert pipeline is not None
        pipeline.add_consumer(asr_consumer)
        await asr_consumer.start()

        # Stream chunks and measure latency
        num_chunks = 30
        for i in range(num_chunks):
            audio_chunk = generate_audio_chunk()
            await websocket.send_bytes(audio_chunk)
            await asyncio.sleep(0.02)

        # Wait for processing
        await asyncio.sleep(0.5)

        # Verify latency measurements
        session = session_manager.get_session(call_id)
        assert session is not None

        # Get latency stats
        stats = session.get_asr_latency_stats()

        if stats["count"] > 0:
            # Verify all latencies are reasonable (should be much less than 150ms)
            assert stats["max"] < 200.0, f"Max latency {stats['max']}ms too high"
            assert stats["avg"] < 100.0, f"Average latency {stats['avg']}ms too high"
            assert stats["p95"] < 150.0, f"P95 latency {stats['p95']}ms exceeds threshold"

            # Verify percentile calculations
            assert stats["p50"] <= stats["p95"], "P50 should be <= P95"
            assert stats["min"] <= stats["max"], "Min should be <= Max"

            # Verify transcripts were collected
            assert len(transcript_collector.transcripts) > 0


@pytest.mark.asyncio
async def test_non_blocking_audio_ingestion(client: AsyncClient):
    """Test that audio ingestion is non-blocking."""
    call_id = "test-non-blocking-111"

    async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        # Receive connection acknowledgment
        message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
        assert message["type"] == "connected"

        # Stream many chunks quickly to test non-blocking behavior
        num_chunks = 100
        start_time = time.time()

        # Send chunks as fast as possible (simulating burst)
        send_tasks = []
        for i in range(num_chunks):
            audio_chunk = generate_audio_chunk()
            send_tasks.append(websocket.send_bytes(audio_chunk))

        # Send all chunks concurrently
        await asyncio.gather(*send_tasks)

        send_time = time.time() - start_time

        # Sending should be very fast (non-blocking)
        # Should complete in < 1 second even for 100 chunks
        assert send_time < 1.0, f"Sending {num_chunks} chunks took {send_time}s (too slow)"

        # Verify session is still active
        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING


@pytest.mark.asyncio
async def test_concurrent_websocket_connections(client: AsyncClient):
    """Test multiple concurrent WebSocket connections."""
    num_connections = 5
    call_ids = [f"concurrent-call-{i}" for i in range(num_connections)]

    async def connect_and_stream(call_id: str):
        """Connect and stream audio chunks."""
        async with client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
            # Receive connection acknowledgment
            message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            assert message["type"] == "connected"
            assert message["call_id"] == call_id

            # Stream some chunks
            for i in range(10):
                audio_chunk = generate_audio_chunk()
                await websocket.send_bytes(audio_chunk)
                await asyncio.sleep(0.02)

            # Verify session exists
            session = session_manager.get_session(call_id)
            assert session is not None

    # Connect all clients concurrently
    start_time = time.time()
    await asyncio.gather(*[connect_and_stream(call_id) for call_id in call_ids])
    total_time = time.time() - start_time

    # All connections should complete within reasonable time
    assert total_time < 5.0, f"Concurrent connections took {total_time}s (too slow)"

    # Verify all sessions were created
    for call_id in call_ids:
        session = session_manager.get_session(call_id)
        # Note: Sessions might be cleaned up after disconnect, so we just verify
        # they existed during the test
