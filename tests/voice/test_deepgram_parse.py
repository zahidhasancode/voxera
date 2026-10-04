"""Deepgram results → transcript events: only a finished speaker ends the turn."""

from app.stt.models import TranscriptType
from app.stt.providers.deepgram_engine import DeepgramStreamingSTTEngine


def result(text: str, *, is_final: bool = False, speech_final: bool = False) -> dict:
    return {
        "type": "Results",
        "is_final": is_final,
        "speech_final": speech_final,
        "channel": {"alternatives": [{"transcript": text, "confidence": 0.93}]},
    }


def engine() -> DeepgramStreamingSTTEngine:
    return DeepgramStreamingSTTEngine(api_key="test")


def test_interim_result_is_partial() -> None:
    ev = engine()._parse_result(result("where is"))
    assert ev.type == TranscriptType.PARTIAL and ev.transcript == "where is"


def test_finished_segment_does_not_end_the_turn() -> None:
    e = engine()
    ev = e._parse_result(result("I would like to know", is_final=True))
    assert ev.type == TranscriptType.PARTIAL
    ev = e._parse_result(result("where my order"))
    assert ev.type == TranscriptType.PARTIAL
    assert ev.transcript == "I would like to know where my order"


def test_speech_final_ends_the_turn_with_all_segments() -> None:
    e = engine()
    e._parse_result(result("I would like to know", is_final=True))
    ev = e._parse_result(result("where my order is.", is_final=True, speech_final=True))
    assert ev.type == TranscriptType.FINAL
    assert ev.transcript == "I would like to know where my order is."
    # next utterance starts clean
    ev = e._parse_result(result("thanks"))
    assert ev.transcript == "thanks"


def test_utterance_end_message_is_the_fallback() -> None:
    e = engine()
    e._parse_result(result("hello there", is_final=True))
    ev = e._parse_result({"type": "UtteranceEnd"})
    assert ev.type == TranscriptType.FINAL and ev.transcript == "hello there"
    assert e._parse_result({"type": "UtteranceEnd"}) is None  # nothing pending: no duplicate final


def test_empty_results_are_ignored() -> None:
    e = engine()
    assert e._parse_result(result("")) is None
    assert e._parse_result(result("", is_final=True, speech_final=True)) is None
    assert e._parse_result({"type": "Metadata"}) is None


def test_final_gets_a_new_utterance_id_next_time() -> None:
    e = engine()
    e._utterance_id = "a"
    first = e._parse_result(result("one.", is_final=True, speech_final=True))
    assert first.utterance_id == "a"
    assert e._utterance_id is None
