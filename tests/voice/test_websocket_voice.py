"""End-to-end: the mounted voice WebSocket with the built-in mock engines (no network)."""

import math
import struct
import time

import pytest
from starlette.testclient import TestClient

from app.core.config import settings

VOICE_WS = f"{settings.API_V1_STR}/"


def tone_frame(amplitude: int = 4000) -> bytes:
    """20 ms of a 440 Hz tone at 16 kHz: audible to the mock recogniser."""
    return struct.pack("<320h", *(int(amplitude * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(320)))


SILENCE = b"\x00" * 640


@pytest.fixture
def client(app, monkeypatch: pytest.MonkeyPatch):
    # Hermetic: never use real providers from a developer's .env in tests.
    for name in ("STT_PROVIDER", "LLM_PROVIDER", "TTS_PROVIDER"):
        monkeypatch.setattr(settings, name, None)
    monkeypatch.setattr(settings, "VOICE_ALLOW_MOCK_PROVIDERS", True)
    with TestClient(app) as c:
        yield c


def read_until(ws, kind: str, limit: int = 3000) -> tuple[list[dict], int]:
    """Read messages until a JSON event of `kind`; return (json events, audio frame count)."""
    events: list[dict] = []
    audio = 0
    for _ in range(limit):
        msg = ws.receive()
        if msg.get("bytes") is not None:
            audio += 1
            continue
        if msg.get("text") is not None:
            import json

            ev = json.loads(msg["text"])
            events.append(ev)
            if ev.get("type") == kind:
                return events, audio
    raise AssertionError(f"no {kind!r} event within {limit} messages; saw {[e.get('type') for e in events][-10:]}")


def test_connection_message_names_the_providers(client) -> None:
    with client.websocket_connect(VOICE_WS) as ws:
        hello = ws.receive_json()
        assert hello["type"] == "connection" and hello["status"] == "connected"
        assert hello["providers"] == {"stt": "mock", "llm": "mock", "tts": "mock"}
        assert hello["audio"] == {"sample_rate": 16000, "frame_ms": 20, "encoding": "pcm_s16le"}


def test_text_turn_produces_tokens_speech_and_metrics(client) -> None:
    with client.websocket_connect(VOICE_WS) as ws:
        ws.receive_json()
        ws.send_json({"type": "dev_test_transcript", "text": "where is my order"})
        events, audio = read_until(ws, "turn_metrics")
        kinds = [e["type"] for e in events]
        assert "llm_partial" in kinds and "llm_final" in kinds
        assert "tts_start" in kinds and "tts_end" in kinds
        assert audio > 0
        metrics = events[-1]
        assert metrics["transcript_final_to_first_audio_ms"] is not None
        assert metrics["interrupted"] is False


def test_audio_in_produces_transcript_and_reply(client) -> None:
    with client.websocket_connect(VOICE_WS) as ws:
        ws.receive_json()
        # Sent at the real 20 ms cadence, like a microphone. (Sent faster than real time, the
        # bounded queue would do its job and drop the oldest frames.)
        for _ in range(50):  # 1 s of sound, then silence so the mock finalises
            ws.send_bytes(tone_frame())
            time.sleep(0.02)
        for _ in range(40):
            ws.send_bytes(SILENCE)
            time.sleep(0.02)
        events, _ = read_until(ws, "llm_final")
        kinds = [e["type"] for e in events]
        assert "partial" in kinds and "final" in kinds
        assert kinds.index("final") < kinds.index("llm_final")


def test_silence_alone_produces_no_transcript(client) -> None:
    """With a live mic the stream is mostly silence; it must not turn into invented speech."""
    with client.websocket_connect(VOICE_WS) as ws:
        ws.receive_json()
        for _ in range(80):
            ws.send_bytes(SILENCE)
        ws.send_json({"type": "ping"})
        events, _ = read_until(ws, "pong")
        assert [e["type"] for e in events] == ["pong"]


def test_ping_pong_and_bad_json(client) -> None:
    with client.websocket_connect(VOICE_WS) as ws:
        ws.receive_json()
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}
        ws.send_text("not json")
        assert ws.receive_json()["type"] == "error"


def test_dev_messages_are_refused_outside_development(client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(type(settings), "voice_dev_messages_enabled", property(lambda self: False))
    with client.websocket_connect(VOICE_WS) as ws:
        ws.receive_json()
        ws.send_json({"type": "dev_test_transcript", "text": "spend my API credit"})
        reply = ws.receive_json()
        assert reply["type"] == "error" and reply["code"] == "dev_message_disabled"


def test_missing_providers_give_a_clear_error_and_release_the_connection(client, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.connection_manager import ws_connection_manager

    monkeypatch.setattr(settings, "VOICE_ALLOW_MOCK_PROVIDERS", False)
    before = len(ws_connection_manager.active_connections)
    with client.websocket_connect(VOICE_WS) as ws:
        err = ws.receive_json()
        assert err["type"] == "error" and err["code"] == "voice_providers_unavailable"
    # The server releases the connection in its own thread, just after the client side closes.
    deadline = time.monotonic() + 2.0
    while len(ws_connection_manager.active_connections) != before and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(ws_connection_manager.active_connections) == before
