"""End-to-end test for WebSocket audio streaming with ASR."""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import pytest

from app.main import create_application
from app.models.call_session import CallState
from app.services.asr import ASRConsumer, MockStreamingASR
from app.services.call_session_manager import session_manager
from app.services.pipeline_manager import pipeline_manager


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    return create_application()


@pytest.fixture
def ws_client(test_app):
    """Sync WebSocket client (Starlette TestClient)."""
    from starlette.testclient import TestClient

    try:
        client_ctx = TestClient(test_app)
    except TypeError as exc:
        pytest.skip(f"Starlette TestClient incompatible with installed httpx: {exc}")

    with client_ctx as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up sessions and pipelines after each test."""
    yield
    session_manager._sessions.clear()
    pipeline_manager._pipelines.clear()


def generate_audio_chunk(size: int = 320) -> bytes:
    """Generate mock PCM audio chunk (20ms at 8kHz, 16-bit)."""
    return b"\x00" * size


class TranscriptCollector:
    """Collects transcript messages from ASR consumer."""

    def __init__(self):
        self.transcripts: List[dict] = []

    async def callback(self, result: dict) -> None:
        self.transcripts.append(result)


def test_websocket_connection(ws_client):
    """Test WebSocket connection establishment."""
    with ws_client.websocket_connect("/api/v1/ws/audio") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "connected"
        assert "call_id" in message
        assert message["status"] == "ready"


def test_audio_chunk_streaming(ws_client):
    """Test streaming audio chunks through WebSocket."""
    call_id = "test-call-123"
    with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "connected"
        assert message["call_id"] == call_id

        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING

        for _ in range(10):
            websocket.send_bytes(generate_audio_chunk())
            time.sleep(0.02)

        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING


@pytest.mark.asyncio
async def test_asr_partial_transcript_emission(ws_client):
    """Test ASR partial transcript emission with latency measurement."""
    call_id = "test-asr-call-456"
    mock_asr = MockStreamingASR(word_probability=0.15)
    transcript_collector = TranscriptCollector()
    asr_consumer = ASRConsumer(
        asr_backend=mock_asr,
        name="test_asr",
        emit_interval_ms=50,
        transcript_callback=transcript_collector.callback,
        latency_threshold_ms=150.0,
        stats_log_interval=5,
    )

    with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "connected"

        pipeline = pipeline_manager.get_pipeline(call_id)
        assert pipeline is not None
        pipeline.add_consumer(asr_consumer)
        await asr_consumer.start()

        num_chunks = 50
        start_time = time.time()
        for _ in range(num_chunks):
            websocket.send_bytes(generate_audio_chunk())
            await asyncio.sleep(0.02)

        await asyncio.sleep(0.5)

        assert len(transcript_collector.transcripts) > 0, "No transcripts were emitted"
        for transcript in transcript_collector.transcripts:
            assert "transcript" in transcript
            assert transcript["type"] == "partial"
            assert transcript["call_id"] == call_id

        session = session_manager.get_session(call_id)
        assert session is not None
        assert len(session.asr_latencies) > 0
        assert max(session.asr_latencies) < 200.0
        assert time.time() - start_time < (num_chunks * 0.02) + 1.0


def test_call_session_lifecycle(ws_client):
    """Test CallSession lifecycle during WebSocket connection."""
    call_id = "test-lifecycle-789"
    with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "connected"

        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING

        for _ in range(5):
            websocket.send_bytes(generate_audio_chunk())
            time.sleep(0.02)

        websocket.send_text(json.dumps({"type": "state_change", "state": "responding"}))
        response = websocket.receive_json()
        assert response["type"] == "state_changed"
        assert response["state"] == "responding"
        assert session_manager.get_session(call_id).state == CallState.RESPONDING

        websocket.send_text(json.dumps({"type": "state_change", "state": "listening"}))
        response = websocket.receive_json()
        assert response["state"] == "listening"
        assert session_manager.get_session(call_id).state == CallState.LISTENING


@pytest.mark.asyncio
async def test_asr_latency_within_bounds(ws_client):
    """Test that ASR latency measurements are within expected bounds."""
    call_id = "test-latency-bounds-999"
    mock_asr = MockStreamingASR(word_probability=0.2)
    transcript_collector = TranscriptCollector()
    asr_consumer = ASRConsumer(
        asr_backend=mock_asr,
        name="test_asr_latency",
        emit_interval_ms=50,
        transcript_callback=transcript_collector.callback,
        latency_threshold_ms=150.0,
        stats_log_interval=3,
    )

    with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        pipeline = pipeline_manager.get_pipeline(call_id)
        pipeline.add_consumer(asr_consumer)
        await asr_consumer.start()

        for _ in range(30):
            websocket.send_bytes(generate_audio_chunk())
            await asyncio.sleep(0.02)
        await asyncio.sleep(0.5)

        session = session_manager.get_session(call_id)
        stats = session.get_asr_latency_stats()
        if stats["count"] > 0:
            assert stats["max"] < 200.0
            assert stats["avg"] < 100.0
            assert stats["p95"] < 150.0
            assert len(transcript_collector.transcripts) > 0


def test_non_blocking_audio_ingestion(ws_client):
    """Test that audio ingestion is non-blocking."""
    call_id = "test-non-blocking-111"
    with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        start_time = time.time()
        for _ in range(100):
            websocket.send_bytes(generate_audio_chunk())
        send_time = time.time() - start_time
        assert send_time < 1.0
        session = session_manager.get_session(call_id)
        assert session is not None
        assert session.state == CallState.LISTENING


def test_concurrent_websocket_connections(ws_client):
    """Test multiple concurrent WebSocket connections."""
    call_ids = [f"concurrent-call-{i}" for i in range(5)]

    def connect_and_stream(call_id: str) -> None:
        with ws_client.websocket_connect(f"/api/v1/ws/audio?call_id={call_id}") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "connected"
            assert message["call_id"] == call_id
            for _ in range(10):
                websocket.send_bytes(generate_audio_chunk())
                time.sleep(0.02)
            assert session_manager.get_session(call_id) is not None

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(connect_and_stream, call_ids))
    assert time.time() - start_time < 5.0
