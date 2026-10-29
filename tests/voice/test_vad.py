"""Voice activity detection and audio-driven barge-in."""

import asyncio
import struct

from app.voice.session import VoiceSession
from app.voice.vad import EnergyVAD
from app.voice.turn_metrics import voice_latency_stats

from tests.voice.fakes import FakeLLM, FakeTTS, Sink, wait_until

SAMPLES = 320  # 20 ms at 16 kHz


def tone(amplitude: int) -> bytes:
    """A 20 ms frame whose mean absolute sample value is about `amplitude`."""
    return struct.pack(f"<{SAMPLES}h", *([amplitude, -amplitude] * (SAMPLES // 2)))


SILENCE = tone(0)
SPEECH = tone(3000)


def test_silence_never_triggers() -> None:
    vad = EnergyVAD()
    assert not any(vad.update(SILENCE) for _ in range(100))


def test_speech_triggers_once_after_the_minimum_run() -> None:
    vad = EnergyVAD(speech_frames=3)
    results = [vad.update(SPEECH) for _ in range(10)]
    assert results == [False, False, True] + [False] * 7


def test_a_single_click_is_ignored() -> None:
    vad = EnergyVAD(speech_frames=3)
    assert not vad.update(SPEECH)
    assert not vad.update(SILENCE)
    assert not vad.update(SPEECH)
    assert not vad.update(SILENCE)


def test_steady_background_noise_raises_the_threshold() -> None:
    vad = EnergyVAD(min_energy=300, noise_ratio=3.0, speech_frames=3, noise_alpha=0.2)
    noise = tone(250)  # below the threshold, learned as background
    for _ in range(100):
        assert not vad.update(noise)
    assert vad.threshold > 600
    # Speech clearly above the learned background still triggers.
    assert [vad.update(SPEECH) for _ in range(3)][-1] is True


def test_speech_can_trigger_again_after_a_pause() -> None:
    vad = EnergyVAD(speech_frames=2)
    assert [vad.update(SPEECH) for _ in range(2)] == [False, True]
    vad.update(SILENCE)
    assert [vad.update(SPEECH) for _ in range(2)] == [False, True]


def _session(sink: Sink, *, vad: bool) -> VoiceSession:
    return VoiceSession(
        llm_engine=FakeLLM("One short answer for you."),
        tts_engine=FakeTTS(frames_per_segment=150),  # 3 s of audio
        send_json=sink.send_json,
        send_bytes=sink.send_bytes,
        vad_barge_in=vad,
    )


async def test_caller_speech_stops_the_reply_without_waiting_for_a_transcript() -> None:
    voice_latency_stats.reset()
    sink = Sink()
    s = _session(sink, vad=True)
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.audio_frames() >= 5)
    assert s.state.is_system_speaking

    for _ in range(3):  # 60 ms of the caller talking, no transcript yet
        await s.process_audio_frame(SPEECH)

    assert sink.json("barge_in")
    assert not s.tts.is_active
    assert not s.state.is_system_speaking
    frames = sink.audio_frames()
    await asyncio.sleep(0.06)
    assert sink.audio_frames() == frames, "no audio may be sent after the interruption"
    assert voice_latency_stats.snapshot()["interruptions"] == 1
    voice_latency_stats.reset()


async def test_speech_while_the_agent_is_silent_does_not_interrupt_anything() -> None:
    sink = Sink()
    s = _session(sink, vad=True)
    for _ in range(5):
        await s.process_audio_frame(SPEECH)
    assert not sink.json("barge_in")


async def test_vad_can_be_switched_off() -> None:
    sink = Sink()
    s = _session(sink, vad=False)
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.audio_frames() >= 5)
    for _ in range(10):
        await s.process_audio_frame(SPEECH)
    assert not sink.json("barge_in")
    assert s.state.is_system_speaking
    await s.close()
