"""Phone call session: streamed reply, return to listening, second turn, barge-in."""

import json

import pytest

from app.stt.models import TranscriptEvent, TranscriptType
from app.telephony import call_session as cs
from app.telephony.call_session import CallSession, CallSessionState

from tests.voice.fakes import FakeLLM, FakeTTS, wait_until


class NullSTT:
    async def process_audio(self, frame):
        return None

    async def finalize_utterance(self):
        return None

    async def reset(self):
        pass

    async def close(self):
        pass


def ev(kind: TranscriptType, text: str, utt: str) -> TranscriptEvent:
    return TranscriptEvent(type=kind, utterance_id=utt, transcript=text, confidence=0.9)


U1 = "11111111-1111-1111-1111-111111111111"
U2 = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
async def call(monkeypatch: pytest.MonkeyPatch):
    llm, tts = FakeLLM("Your order shipped today. It arrives on Friday."), FakeTTS(frames_per_segment=4)
    monkeypatch.setattr(cs, "build_stt_engine", lambda: NullSTT())
    monkeypatch.setattr(cs, "build_llm_engine", lambda: llm)
    monkeypatch.setattr(cs, "build_tts_engine", lambda: tts)
    sent: list[dict] = []

    async def send_text(msg: str) -> None:
        sent.append(json.loads(msg))

    session = CallSession(call_sid="CA1", stream_sid="MZ1")
    await session.start(send_text=send_text)
    yield session, llm, tts, sent
    await session.stop()


async def say(session: CallSession, text: str, utt: str) -> None:
    await session.turn_manager.process_transcript_event(ev(TranscriptType.PARTIAL, text, utt))
    await session.turn_manager.process_transcript_event(ev(TranscriptType.FINAL, text, utt))


async def test_reply_is_spoken_per_sentence_and_call_returns_to_listening(call) -> None:
    session, llm, tts, sent = call
    await say(session, "where is my order", U1)
    await wait_until(lambda: session.state == CallSessionState.SPEAKING)
    await wait_until(lambda: session.state == CallSessionState.LISTENING)
    assert tts.segments == ["Your order shipped today.", "It arrives on Friday."]
    media = [m for m in sent if m.get("event") == "media"]
    assert len(media) == 8 and all(m["streamSid"] == "MZ1" for m in media)


async def test_second_turn_is_answered_with_history(call) -> None:
    """Before the fix the call stayed in SPEAKING after the first answer and ignored the caller."""
    session, llm, _tts, _sent = call
    await say(session, "where is my order", U1)
    await wait_until(lambda: session.state == CallSessionState.SPEAKING)
    await wait_until(lambda: session.state == CallSessionState.LISTENING)
    await say(session, "when does it arrive", U2)
    await wait_until(lambda: len(llm.calls) == 2)
    assert llm.calls[1]["history"][0] == {"role": "user", "content": "where is my order"}
    assert llm.calls[1]["history"][1]["role"] == "assistant"


async def test_barge_in_sends_twilio_clear(call) -> None:
    session, _llm, tts, sent = call
    tts.frames_per_segment = 200
    await say(session, "where is my order", U1)
    await wait_until(lambda: any(m.get("event") == "media" for m in sent))
    await session.turn_manager.process_transcript_event(ev(TranscriptType.PARTIAL, "wait", U2))
    await wait_until(lambda: any(m.get("event") == "clear" for m in sent))
    assert session.state == CallSessionState.LISTENING
    assert not session.tts_consumer.is_active
