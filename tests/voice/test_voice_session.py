"""The voice session: what happens between a finished user sentence and a heard reply."""

import asyncio

import pytest

from app.stt.models import TranscriptEvent, TranscriptType
from app.voice.session import VoiceSession
from app.voice.turn_metrics import voice_latency_stats

from tests.voice.fakes import FakeLLM, FakeTTS, Sink, wait_until


def make_session(sink: Sink, llm: FakeLLM, tts: FakeTTS, **kw) -> VoiceSession:
    return VoiceSession(llm_engine=llm, tts_engine=tts, send_json=sink.send_json, send_bytes=sink.send_bytes, **kw)


def partial(text: str, utt: str = "11111111-1111-1111-1111-111111111111") -> TranscriptEvent:
    return TranscriptEvent(type=TranscriptType.PARTIAL, utterance_id=utt, transcript=text, confidence=0.9)


def final(text: str, utt: str = "11111111-1111-1111-1111-111111111111") -> TranscriptEvent:
    return TranscriptEvent(type=TranscriptType.FINAL, utterance_id=utt, transcript=text, confidence=0.9)


@pytest.fixture(autouse=True)
def _reset_stats():
    voice_latency_stats.reset()
    yield
    voice_latency_stats.reset()


async def test_speech_starts_before_the_llm_has_finished() -> None:
    """Sentence streaming: the first audio frame goes out before llm_final."""
    sink = Sink()
    llm = FakeLLM("This is the first sentence. " + "And then a much longer second sentence follows it. " * 4, token_delay=0.004)
    tts = FakeTTS(frames_per_segment=3)
    s = make_session(sink, llm, tts)
    await s.inject_transcript("where is my order")
    await wait_until(lambda: sink.json("turn_metrics"))
    types = sink.types()
    assert types.index("audio") < types.index("llm_final")
    assert tts.segments[0] == "This is the first sentence."
    assert len(tts.segments) >= 3  # spoken sentence by sentence, not as one block


async def test_system_turn_lasts_until_playback_ends() -> None:
    sink = Sink()
    llm, tts = FakeLLM("One short answer for you."), FakeTTS(frames_per_segment=25)  # 0.5 s of audio
    s = make_session(sink, llm, tts)
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.json("llm_final"))
    await wait_until(lambda: sink.audio_frames() >= 5)
    assert not s.llm.is_generating
    assert s.state.is_system_speaking, "the reply is still playing, so the system is still speaking"
    await wait_until(lambda: sink.json("tts_end"))
    await wait_until(lambda: not s.state.is_system_speaking)


async def test_barge_in_during_playback_stops_the_voice() -> None:
    """The original bug: after the LLM finished, user speech no longer stopped the audio."""
    sink = Sink()
    llm, tts = FakeLLM("One short answer for you."), FakeTTS(frames_per_segment=150)  # 3 s of audio
    s = make_session(sink, llm, tts)
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.json("llm_final"))
    await wait_until(lambda: sink.audio_frames() >= 5)

    await s.process_transcript_event(partial("wait", utt="22222222-2222-2222-2222-222222222222"))

    assert sink.json("tts_clear"), "client must be told to drop buffered audio"
    assert sink.json("barge_in")
    assert not s.tts.is_active
    assert not s.state.is_system_speaking
    assert s.state.is_user_speaking
    frames = sink.audio_frames()
    await asyncio.sleep(0.06)
    assert sink.audio_frames() == frames, "no audio may be sent after the interruption"
    assert frames < 150
    assert voice_latency_stats.snapshot()["interruptions"] == 1


async def test_barge_in_during_generation_cancels_the_llm() -> None:
    sink = Sink()
    llm = FakeLLM("word " * 200, token_delay=0.005)
    s = make_session(sink, llm, FakeTTS())
    await s.inject_transcript("tell me everything")
    await wait_until(lambda: sink.json("llm_partial"))
    await s.process_transcript_event(partial("stop", utt="22222222-2222-2222-2222-222222222222"))
    await wait_until(lambda: sink.json("llm_cancelled"))
    assert not s.llm.is_generating
    assert not sink.json("llm_final")


async def test_second_turn_receives_the_conversation_so_far() -> None:
    sink = Sink()
    llm, tts = FakeLLM("Your order shipped today."), FakeTTS(frames_per_segment=1)
    s = make_session(sink, llm, tts)
    await s.inject_transcript("where is my order")
    await wait_until(lambda: len(sink.json("turn_metrics")) == 1)
    await s.inject_transcript("when will it arrive")
    await wait_until(lambda: len(sink.json("turn_metrics")) == 2)
    assert llm.calls[0] == {"prompt": "where is my order", "history": []}
    assert llm.calls[1]["prompt"] == "when will it arrive"
    assert llm.calls[1]["history"] == [
        {"role": "user", "content": "where is my order"},
        {"role": "assistant", "content": "Your order shipped today."},
    ]


async def test_history_is_bounded() -> None:
    sink = Sink()
    s = make_session(sink, FakeLLM("Okay then, noted."), FakeTTS(frames_per_segment=1), history_turns=2)
    for i in range(5):
        await s.inject_transcript(f"question number {i}")
        await wait_until(lambda n=i: len(sink.json("turn_metrics")) == n + 1)
    assert len(s.history) == 4
    assert s.history[0]["content"] == "question number 3"


async def test_final_without_partial_is_still_answered() -> None:
    sink = Sink()
    llm = FakeLLM("Yes, of course I can.")
    s = make_session(sink, llm, FakeTTS(frames_per_segment=1))
    await s.process_transcript_event(final("yes"))
    await wait_until(lambda: sink.json("turn_metrics"))
    assert llm.calls and llm.calls[0]["prompt"] == "yes"


async def test_turn_metrics_report_first_token_and_first_audio() -> None:
    sink = Sink()
    s = make_session(sink, FakeLLM("A full sentence of reply text."), FakeTTS(frames_per_segment=2))
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.json("turn_metrics"))
    m = sink.json("turn_metrics")[0]
    assert m["transcript_final_to_llm_first_token_ms"] is not None
    assert m["transcript_final_to_first_audio_ms"] >= m["transcript_final_to_llm_first_token_ms"]
    assert m["interrupted"] is False
    snap = voice_latency_stats.snapshot()
    assert snap["turns"] == 1 and snap["samples"] == 1


async def test_llm_failure_reports_error_and_frees_the_turn() -> None:
    sink = Sink()
    llm = FakeLLM()
    llm.fail = True
    s = make_session(sink, llm, FakeTTS())
    await s.inject_transcript("hello")
    await wait_until(lambda: [e for e in sink.json("error") if e.get("code") == "llm_failed"])
    await wait_until(lambda: not s.state.is_system_speaking)
    assert sink.audio_frames() == 0


async def test_close_stops_everything() -> None:
    sink = Sink()
    s = make_session(sink, FakeLLM("word " * 100, token_delay=0.005), FakeTTS(frames_per_segment=100))
    await s.inject_transcript("hello")
    await wait_until(lambda: sink.json("llm_partial"))
    await s.close()
    assert not s.llm.is_generating and not s.tts.is_active
