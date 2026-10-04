"""Speech consumer: segment queue, real-time pacing and stopping."""

import asyncio
import time

from app.tts.tts_consumer import TTSConsumer

from tests.voice.fakes import FakeTTS, Sink, wait_until


def make(sink: Sink, tts: FakeTTS, ended: list, **kw) -> TTSConsumer:
    async def on_end(utterance_id: str, interrupted: bool) -> None:
        ended.append((utterance_id, interrupted))

    return TTSConsumer(tts, sink.send_bytes, sink.send_json, sample_rate=16000, on_playback_end=on_end, **kw)


async def test_segments_are_spoken_in_order() -> None:
    sink, tts, ended = Sink(), FakeTTS(frames_per_segment=3), []
    c = make(sink, tts, ended)
    await c.begin("u1")
    await c.speak("First sentence.")
    await c.speak("Second sentence.")
    await c.finish()
    await wait_until(lambda: ended)
    assert tts.segments == ["First sentence.", "Second sentence."]
    assert sink.audio_frames() == 6
    assert sink.types()[0] == "tts_start"
    assert "tts_end" in sink.types()
    assert ended == [("u1", False)]
    assert not c.is_active


async def test_stays_active_until_audio_has_played() -> None:
    """10 frames = 200 ms of audio: the reply is not over the moment the last frame is sent."""
    sink, tts, ended = Sink(), FakeTTS(frames_per_segment=10), []
    c = make(sink, tts, ended)
    start = time.monotonic()
    await c.start_speaking("Ten frames of audio here.", "u1")
    await wait_until(lambda: sink.audio_frames() == 10)
    assert c.is_active and not ended
    await wait_until(lambda: ended)
    assert time.monotonic() - start >= 0.18


async def test_audio_is_paced_not_dumped() -> None:
    """With 2 s of audio available instantly, only about max_lead may be sent ahead of playback."""
    sink, tts, ended = Sink(), FakeTTS(frames_per_segment=100), []
    c = make(sink, tts, ended, max_lead_seconds=0.1)
    await c.start_speaking("A long answer.", "u1")
    await asyncio.sleep(0.2)
    sent = sink.audio_frames()
    assert 5 <= sent <= 20, sent  # roughly (0.2 s elapsed + 0.1 s lead) / 20 ms
    await c.stop()


async def test_stop_clears_client_buffer_and_reports_interruption() -> None:
    sink, tts, ended = Sink(), FakeTTS(frames_per_segment=100), []
    c = make(sink, tts, ended)
    await c.start_speaking("A long answer.", "u1")
    await wait_until(lambda: sink.audio_frames() >= 3)
    assert await c.stop(reason="barge_in") is True
    frames_at_stop = sink.audio_frames()
    assert sink.json("tts_clear") == [{"type": "tts_clear", "utterance_id": "u1", "reason": "barge_in"}]
    assert ended == [("u1", True)]
    await asyncio.sleep(0.05)
    assert sink.audio_frames() == frames_at_stop  # nothing more after the stop
    assert frames_at_stop < 100


async def test_stop_without_active_reply_is_a_noop() -> None:
    sink, ended = Sink(), []
    c = make(sink, FakeTTS(), ended)
    assert await c.stop() is False
    assert sink.events == []


async def test_begin_supersedes_previous_reply() -> None:
    sink, tts, ended = Sink(), FakeTTS(frames_per_segment=100), []
    c = make(sink, tts, ended)
    await c.start_speaking("Old answer.", "u1")
    await wait_until(lambda: sink.audio_frames() >= 2)
    await c.start_speaking("New.", "u2")
    await wait_until(lambda: ("u1", True) in ended)
    assert c.current_utterance_id == "u2"
    await c.stop()
