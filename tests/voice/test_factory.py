"""Voice factory tests."""

import pytest

from app.core.enums import LLMProviderType, STTProviderType, TTSProviderType


def test_build_stt_requires_deepgram_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.voice.factory import build_stt_engine

    monkeypatch.setattr("app.voice.factory.settings.STT_PROVIDER", STTProviderType.DEEPGRAM)
    monkeypatch.setattr("app.voice.factory.settings.DEEPGRAM_API_KEY", None)
    with pytest.raises(ValueError, match="DEEPGRAM_API_KEY"):
        build_stt_engine()


def test_build_llm_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.voice.factory import build_llm_engine

    monkeypatch.setattr("app.voice.factory.settings.LLM_PROVIDER", LLMProviderType.OPENAI)
    monkeypatch.setattr("app.voice.factory.settings.VOICE_OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.voice.factory.settings.OPENAI_API_KEY", None)
    engine = build_llm_engine()
    assert engine.__class__.__name__ == "OpenAIStreamingLLMEngine"


def test_build_tts_elevenlabs(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.voice.factory import build_tts_engine

    monkeypatch.setattr("app.voice.factory.settings.TTS_PROVIDER", TTSProviderType.ELEVENLABS)
    monkeypatch.setattr("app.voice.factory.settings.ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr("app.voice.factory.settings.VOICE_TTS_VOICE_ID", "voice123")
    engine = build_tts_engine()
    assert engine.__class__.__name__ == "ElevenLabsStreamingTTSEngine"
