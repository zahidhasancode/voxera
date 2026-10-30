"""Smarter end of turn: an unfinished-sounding transcript waits for the caller to go on."""

import asyncio
import uuid

import pytest

from app.stt.models import TranscriptEvent, TranscriptType
from app.voice.end_of_turn import sounds_unfinished
from app.voice.session import VoiceSession

from tests.voice.fakes import FakeLLM, FakeTTS, Sink, wait_until
from tests.voice.test_vad import SPEECH


@pytest.mark.parametrize(
    "text",
    ["I want to book a table for", "Can you help me with", "my order number is 4, and", "um.", "I was thinking..."],
)
def test_unfinished_sentences(text: str) -> None:
    assert sounds_unfinished(text)


@pytest.mark.parametrize(
    "text",
    ["What is the time?", "Thank you.", "Where is my order", "I think so.", "Turn it on", "hello", "", "Is it for?"],
)
def test_finished_sentences(text: str) -> None:
    assert not sounds_unfinished(text)


def _session(sink: Sink, llm: FakeLLM, *, hold_ms: int = 100) -> VoiceSession:
    return VoiceSession(
        llm_engine=llm,
        tts_engine=FakeTTS(frames_per_segment=3),
        send_json=sink.send_json,
        send_bytes=sink.send_bytes,
        eot_hold_ms=hold_ms,
    )


def _id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


async def _say(s: VoiceSession, text: str, utt: str) -> None:
    utt = _id(utt)
    for kind in (TranscriptType.PARTIAL, TranscriptType.FINAL):
        await s.process_transcript_event(TranscriptEvent(type=kind, utterance_id=utt, transcript=text, confidence=0.9))


async def test_a_finished_sentence_is_answered_at_once() -> None:
    sink, llm = Sink(), FakeLLM("Sure.")
    s = _session(sink, llm, hold_ms=1000)
    await _say(s, "What is the time?", "u1")
    await wait_until(lambda: llm.calls, timeout=0.5)  # well inside the 1 s hold
    assert [c["prompt"] for c in llm.calls] == ["What is the time?"]
    assert not sink.json("turn_held")
    await s.close()


async def test_the_continuation_joins_the_held_turn() -> None:
    sink, llm = Sink(), FakeLLM("Booked.")
    s = _session(sink, llm, hold_ms=500)
    await _say(s, "I want to book a table for", "u1")
    assert sink.json("turn_held") == [{"type": "turn_held", "utterance_id": _id("u1")}]
    assert llm.calls == []
    await asyncio.sleep(0.05)  # the caller pauses, then goes on
    await _say(s, "four people tonight.", "u2")
    await wait_until(lambda: llm.calls)
    assert [c["prompt"] for c in llm.calls] == ["I want to book a table for four people tonight."]
    await asyncio.sleep(0.6)  # the old timer must not fire a second reply
    assert len(llm.calls) == 1
    await s.close()


async def test_silence_after_a_held_turn_still_gets_an_answer() -> None:
    sink, llm = Sink(), FakeLLM("Sure.")
    s = _session(sink, llm, hold_ms=100)
    await _say(s, "Can you help me with", "u1")
    await asyncio.sleep(0.03)
    assert llm.calls == []
    await wait_until(lambda: llm.calls, timeout=1.0)
    assert [c["prompt"] for c in llm.calls] == ["Can you help me with"]
    await wait_until(lambda: sink.json("turn_metrics"))
    await s.close()


async def test_speech_onset_during_the_hold_restarts_the_wait() -> None:
    sink, llm = Sink(), FakeLLM("Sure.")
    s = VoiceSession(
        llm_engine=llm,
        tts_engine=FakeTTS(frames_per_segment=3),
        send_json=sink.send_json,
        send_bytes=sink.send_bytes,
        eot_hold_ms=150,
        vad_barge_in=True,
    )
    await _say(s, "I need it for", "u1")
    await asyncio.sleep(0.1)
    for _ in range(3):  # the caller starts talking again, no transcript yet
        await s.process_audio_frame(SPEECH)
    await asyncio.sleep(0.1)  # past the first deadline, inside the restarted one
    assert llm.calls == []
    await _say(s, "Friday.", "u2")
    await wait_until(lambda: llm.calls)
    assert [c["prompt"] for c in llm.calls] == ["I need it for Friday."]
    await s.close()


async def test_the_hold_can_be_switched_off() -> None:
    sink, llm = Sink(), FakeLLM("Sure.")
    s = _session(sink, llm, hold_ms=0)
    await _say(s, "I want to book a table for", "u1")
    await wait_until(lambda: llm.calls, timeout=0.5)
    assert [c["prompt"] for c in llm.calls] == ["I want to book a table for"]
    await s.close()


async def test_closing_drops_a_held_turn() -> None:
    sink, llm = Sink(), FakeLLM("Sure.")
    s = _session(sink, llm, hold_ms=50)
    await _say(s, "and", "u1")
    await s.close()
    await asyncio.sleep(0.1)
    assert llm.calls == []
