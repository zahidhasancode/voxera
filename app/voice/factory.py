"""Voice provider factory."""

from __future__ import annotations

from app.core.config import settings
from app.core.enums import LLMProviderType, STTProviderType, TTSProviderType
from app.llm.providers.anthropic_engine import AnthropicStreamingLLMEngine
from app.llm.providers.failover_engine import FailoverStreamingLLMEngine
from app.llm.providers.groq_engine import GroqStreamingLLMEngine
from app.llm.providers.openai_engine import OpenAIStreamingLLMEngine
from app.llm.streaming_engine import StreamingLLMEngine
from app.stt.engine import StreamingSTTEngine
from app.stt.providers.deepgram_engine import DeepgramStreamingSTTEngine
from app.tts.providers.elevenlabs_engine import ElevenLabsStreamingTTSEngine
from app.tts.providers.openai_tts_engine import OpenAIStreamingTTSEngine
from app.tts.streaming_engine import StreamingTTSEngine


def build_stt_engine(*, partial_interval: int = 1) -> StreamingSTTEngine:
    provider = settings.STT_PROVIDER
    if not provider:
        raise ValueError("STT_PROVIDER must be configured")
    provider_id = STTProviderType(provider)
    if provider_id == STTProviderType.DEEPGRAM:
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is required for Deepgram STT")
        return DeepgramStreamingSTTEngine(api_key=settings.DEEPGRAM_API_KEY)
    raise ValueError(f"Unsupported STT provider: {provider_id}")


def build_llm_engine() -> StreamingLLMEngine:
    provider = settings.LLM_PROVIDER
    if not provider:
        raise ValueError("LLM_PROVIDER must be configured")
    primary = _build_single_llm(LLMProviderType(provider))
    failover = None
    if settings.VOICE_LLM_FAILOVER_PROVIDER:
        failover = _build_single_llm(LLMProviderType(settings.VOICE_LLM_FAILOVER_PROVIDER))
    if failover is not None:
        return FailoverStreamingLLMEngine(primary, failover)
    return primary


def _build_single_llm(provider_id: LLMProviderType) -> StreamingLLMEngine:
    if provider_id == LLMProviderType.OPENAI:
        api_key = settings.voice_openai_api_key
        if not api_key:
            raise ValueError("VOICE_OPENAI_API_KEY or OPENAI_API_KEY is required")
        return OpenAIStreamingLLMEngine(api_key=api_key)
    if provider_id == LLMProviderType.ANTHROPIC:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required")
        return AnthropicStreamingLLMEngine(api_key=settings.ANTHROPIC_API_KEY)
    if provider_id == LLMProviderType.AZURE_OPENAI:
        if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI credentials required")
        deployment = settings.AZURE_OPENAI_CHAT_DEPLOYMENT or settings.VOICE_LLM_MODEL
        api_base = f"{settings.AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{deployment}"
        return OpenAIStreamingLLMEngine(
            api_key=settings.AZURE_OPENAI_API_KEY,
            model=deployment,
            api_base=api_base,
            extra_headers={"api-key": settings.AZURE_OPENAI_API_KEY},
        )
    if provider_id == LLMProviderType.GROQ:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        return GroqStreamingLLMEngine(api_key=settings.GROQ_API_KEY)
    if provider_id == LLMProviderType.GEMINI:
        raise ValueError("Gemini voice LLM provider is not yet implemented")
    raise ValueError(f"Unsupported LLM provider: {provider_id}")


def build_tts_engine(*, voice_id: str | None = None) -> StreamingTTSEngine:
    provider = settings.TTS_PROVIDER
    if not provider:
        raise ValueError("TTS_PROVIDER must be configured")
    provider_id = TTSProviderType(provider)
    selected_voice = voice_id or settings.VOICE_TTS_VOICE_ID
    if provider_id == TTSProviderType.ELEVENLABS:
        if not settings.ELEVENLABS_API_KEY or not selected_voice:
            raise ValueError("ELEVENLABS_API_KEY and VOICE_TTS_VOICE_ID are required")
        return ElevenLabsStreamingTTSEngine(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=selected_voice,
        )
    if provider_id == TTSProviderType.OPENAI_AUDIO:
        api_key = settings.voice_openai_api_key
        if not api_key:
            raise ValueError("VOICE_OPENAI_API_KEY or OPENAI_API_KEY is required")
        return OpenAIStreamingTTSEngine(api_key=api_key, voice=selected_voice)
    raise ValueError(f"Unsupported TTS provider: {provider_id}")
