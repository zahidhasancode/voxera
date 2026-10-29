"""AWS voice engines (Transcribe, Bedrock, Polly) with fake clients: no network, no AWS account."""

import asyncio
from types import SimpleNamespace as NS

import pytest

from app.core.enums import LLMProviderType, STTProviderType, TTSProviderType
from app.llm.providers.bedrock_engine import BedrockStreamingLLMEngine
from app.stt.models import TranscriptType
from app.stt.providers.aws_transcribe_engine import AmazonTranscribeSTTEngine
from app.tts.providers.polly_engine import PollyStreamingTTSEngine


# ---------- Transcribe ----------

def _transcript(*results):
    return NS(results=[NS(is_partial=p, alternatives=[NS(transcript=t)]) for p, t in results])


def test_transcribe_maps_partial_and_final_results():
    eng = AmazonTranscribeSTTEngine(client_factory=lambda: None)
    eng._utterance_id = "u1"
    events = eng.parse_results(_transcript((True, "hello"), (False, "hello there.")))
    assert [e.type for e in events] == [TranscriptType.PARTIAL, TranscriptType.FINAL]
    assert [e.transcript for e in events] == ["hello", "hello there."]
    assert all(e.utterance_id == "u1" for e in events)
    assert eng._utterance_id is None  # a final result closes the utterance


def test_transcribe_ignores_empty_results():
    eng = AmazonTranscribeSTTEngine(client_factory=lambda: None)
    assert eng.parse_results(_transcript((True, "  "))) == []
    assert eng.parse_results(None) == []


class _FakeTranscribeStream:
    def __init__(self, script):
        self.sent: list[bytes] = []
        self.ended = False
        self._script = script
        outer = self

        class Input:
            async def send_audio_event(self, audio_chunk):
                outer.sent.append(audio_chunk)

            async def end_stream(self):
                outer.ended = True

        self.input_stream = Input()

    @property
    def output_stream(self):
        async def gen():
            for item in self._script:
                await asyncio.sleep(0.01)
                yield NS(transcript=item)

        return gen()


class _FakeTranscribeClient:
    def __init__(self, stream):
        self.stream = stream
        self.args = None

    async def start_stream_transcription(self, **kwargs):
        self.args = kwargs
        return self.stream


async def test_transcribe_streams_frames_and_returns_the_final_transcript():
    stream = _FakeTranscribeStream([_transcript((True, "what is")), _transcript((False, "What is the time?"))])
    client = _FakeTranscribeClient(stream)
    eng = AmazonTranscribeSTTEngine(client_factory=lambda: client, sample_rate=16000, language="en-US")
    for _ in range(3):
        await eng.process_audio(b"\x00" * 640)
    final = await eng.finalize_utterance()
    assert client.args == {"language_code": "en-US", "media_sample_rate_hz": 16000, "media_encoding": "pcm"}
    assert len(stream.sent) == 3 and stream.ended
    assert final is not None and final.type == TranscriptType.FINAL
    assert final.transcript == "What is the time?"


# ---------- Bedrock ----------

class _FakeBedrock:
    def __init__(self, deltas, delay=0.0):
        self.deltas = deltas
        self.delay = delay
        self.request = None
        self.closed = False

    def converse_stream(self, **kwargs):
        import time

        self.request = kwargs
        fake = self

        class Stream:
            def __iter__(self):
                yield {"messageStart": {"role": "assistant"}}
                for d in fake.deltas:
                    time.sleep(fake.delay)
                    yield {"contentBlockDelta": {"delta": {"text": d}}}
                yield {"messageStop": {"stopReason": "end_turn"}}

            def close(self):
                fake.closed = True

        return {"stream": Stream()}


async def test_bedrock_streams_tokens_in_order_with_history():
    fake = _FakeBedrock(["Hello", " there", "."])
    eng = BedrockStreamingLLMEngine(model_id="m", region="eu-west-1", system_prompt="sys", max_tokens=64, client=fake)
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
    tokens = [t.token async for t in eng.stream("how are you?", history=history)]
    assert tokens == ["Hello", " there", "."]
    assert fake.request["modelId"] == "m"
    assert fake.request["system"] == [{"text": "sys"}]
    assert [m["role"] for m in fake.request["messages"]] == ["user", "assistant", "user"]
    assert fake.request["messages"][-1]["content"] == [{"text": "how are you?"}]
    assert eng.last_metrics().token_count == 3


async def test_bedrock_errors_reach_the_consumer():
    class Broken:
        def converse_stream(self, **kwargs):
            raise RuntimeError("AccessDeniedException")

    eng = BedrockStreamingLLMEngine(model_id="m", region="r", client=Broken())
    with pytest.raises(RuntimeError, match="AccessDenied"):
        async for _ in eng.stream("x"):
            pass


async def test_bedrock_cancellation_stops_the_stream():
    fake = _FakeBedrock(["a"] * 50, delay=0.01)
    eng = BedrockStreamingLLMEngine(model_id="m", region="r", client=fake)
    got: list[str] = []

    async def consume():
        async for t in eng.stream("x"):
            got.append(t.token)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert 0 < len(got) < 50
    assert fake.closed


# ---------- Polly ----------

class _FakePolly:
    def __init__(self, audio: bytes):
        self.audio = audio
        self.request = None

    def synthesize_speech(self, **kwargs):
        import io

        self.request = kwargs
        return {"AudioStream": io.BytesIO(self.audio)}


async def test_polly_yields_fixed_size_pcm_frames():
    frame = 640  # 20 ms of 16 kHz PCM16
    fake = _FakePolly(b"\x01\x00" * (frame * 3 + 100))  # 3.x frames worth of samples
    eng = PollyStreamingTTSEngine(voice_id="Joanna", engine="neural", region="r", sample_rate=16000, frame_ms=20, client=fake)
    frames = [f async for f in eng.stream("Hello.", utterance_id="u")]
    assert all(len(f) == frame for f in frames)
    assert len(frames) == 7  # 6.15 frames of audio, the last one padded
    assert fake.request == {"Text": "Hello.", "VoiceId": "Joanna", "Engine": "neural", "OutputFormat": "pcm", "SampleRate": "16000"}
    assert eng.last_metrics().frame_count == 7


def test_polly_rejects_unsupported_sample_rates():
    with pytest.raises(ValueError, match="8000 or 16000"):
        PollyStreamingTTSEngine(sample_rate=24000, client=object())


# ---------- factory ----------

def test_factory_builds_aws_engines(monkeypatch):
    from app.voice import factory

    monkeypatch.setattr("app.voice.factory.settings.STT_PROVIDER", STTProviderType.AMAZON_TRANSCRIBE)
    monkeypatch.setattr("app.voice.factory.settings.LLM_PROVIDER", LLMProviderType.BEDROCK)
    monkeypatch.setattr("app.voice.factory.settings.TTS_PROVIDER", TTSProviderType.AMAZON_POLLY)
    monkeypatch.setattr("app.voice.factory.settings.VOICE_LLM_FAILOVER_PROVIDER", None)
    assert type(factory.build_stt_engine()).__name__ == "AmazonTranscribeSTTEngine"
    assert type(factory.build_llm_engine()).__name__ == "BedrockStreamingLLMEngine"
    assert type(factory.build_tts_engine()).__name__ == "PollyStreamingTTSEngine"
