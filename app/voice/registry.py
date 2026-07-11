"""Voice platform startup validation."""

from __future__ import annotations

from app.core.config import settings
from app.core.logger import get_logger
from app.voice.factory import build_llm_engine, build_stt_engine, build_tts_engine

logger = get_logger(__name__)


async def validate_voice_platform() -> None:
    """Fail fast when voice providers are misconfigured."""
    if not settings.VOICE_REQUIRE_PROVIDERS and not (
        settings.STT_PROVIDER or settings.LLM_PROVIDER or settings.TTS_PROVIDER
    ):
        logger.info("Voice providers not configured — voice endpoints will fail until configured")
        return

    if settings.VOICE_REQUIRE_PROVIDERS or settings.is_production:
        for name, value in (
            ("STT_PROVIDER", settings.STT_PROVIDER),
            ("LLM_PROVIDER", settings.LLM_PROVIDER),
            ("TTS_PROVIDER", settings.TTS_PROVIDER),
        ):
            if not value:
                raise RuntimeError(f"{name} must be set in production")

    stt = build_stt_engine() if settings.STT_PROVIDER else None
    llm = build_llm_engine() if settings.LLM_PROVIDER else None
    tts = build_tts_engine() if settings.TTS_PROVIDER else None

    if stt is not None:
        logger.info("Validating STT provider", extra_fields={"provider": settings.STT_PROVIDER})
        await stt.validate_connection()
        await stt.close()

    if llm is not None:
        logger.info("Validating LLM provider", extra_fields={"provider": settings.LLM_PROVIDER})
        await llm.validate_connection()

    if tts is not None:
        logger.info("Validating TTS provider", extra_fields={"provider": settings.TTS_PROVIDER})
        await tts.validate_connection()

    logger.info(
        "Voice platform validated",
        extra_fields={
            "stt_provider": settings.STT_PROVIDER,
            "llm_provider": settings.LLM_PROVIDER,
            "tts_provider": settings.TTS_PROVIDER,
            "sample_rate": settings.VOICE_SAMPLE_RATE,
            "frame_bytes": settings.VOICE_PCM_FRAME_BYTES,
        },
    )
