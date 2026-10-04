"""OpenAI speech API streaming TTS engine."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.tts.streaming_engine import TTSAudioMetrics, StreamingTTSEngine
from app.voice.audio import Pcm16Resampler, chunk_pcm_bytes
from app.voice.http import get_http_client

logger = get_logger(__name__)

# Sample rate of OpenAI's `response_format: "pcm"` output.
OPENAI_PCM_SAMPLE_RATE = 24000


class OpenAIStreamingTTSEngine(StreamingTTSEngine):
    """Streams PCM16 audio from OpenAI /v1/audio/speech."""

    def __init__(
        self,
        *,
        api_key: str,
        voice: str | None = None,
        model: str | None = None,
        api_base: str | None = None,
        frame_bytes: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._voice = voice or settings.VOICE_TTS_VOICE_ID or "alloy"
        self._model = model or settings.VOICE_TTS_MODEL
        self._api_base = (api_base or settings.OPENAI_API_BASE).rstrip("/")
        self._frame_bytes = frame_bytes or settings.VOICE_PCM_FRAME_BYTES
        self._last_metrics = TTSAudioMetrics()

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self._api_base}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()

    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        start = time.monotonic()
        first_audio_time: float | None = None
        frame_count = 0
        payload = {
            "model": self._model,
            "input": text,
            "voice": self._voice,
            "response_format": "pcm",
        }
        try:
            client = get_http_client()
            async with client.stream(
                "POST",
                f"{self._api_base}/audio/speech",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                buffer = bytearray()
                # OpenAI returns raw PCM16 at 24 kHz; the pipeline runs at VOICE_SAMPLE_RATE.
                resampler = Pcm16Resampler(OPENAI_PCM_SAMPLE_RATE, settings.VOICE_SAMPLE_RATE)
                async for chunk in response.aiter_bytes():
                    if not chunk:
                        continue
                    buffer.extend(resampler.process(chunk))
                    frames, remainder = chunk_pcm_bytes(bytes(buffer), self._frame_bytes)
                    buffer = bytearray(remainder)
                    for frame in frames:
                        if first_audio_time is None:
                            first_audio_time = time.monotonic()
                        frame_count += 1
                        yield frame
                if buffer:
                    padded = bytes(buffer).ljust(self._frame_bytes, b"\x00")
                    if first_audio_time is None:
                        first_audio_time = time.monotonic()
                    frame_count += 1
                    yield padded[: self._frame_bytes]
        except asyncio.CancelledError:
            logger.info(
                "OpenAI TTS cancelled",
                extra_fields={"utterance_id": utterance_id, "frames_emitted": frame_count},
            )
            raise
        finally:
            end = time.monotonic()
            ttfa = (first_audio_time - start) * 1000.0 if first_audio_time else 0.0
            total_ms = (end - start) * 1000.0
            fps = frame_count / (total_ms / 1000.0) if total_ms > 0 else 0.0
            self._last_metrics = TTSAudioMetrics(
                time_to_first_audio_ms=ttfa,
                total_audio_ms=total_ms,
                frame_count=frame_count,
                frames_per_second=fps,
            )

    def last_metrics(self) -> TTSAudioMetrics:
        return self._last_metrics
