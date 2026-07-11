"""ElevenLabs streaming TTS engine."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.tts.streaming_engine import TTSAudioMetrics, StreamingTTSEngine
from app.voice.audio import chunk_pcm_bytes

logger = get_logger(__name__)


class ElevenLabsStreamingTTSEngine(StreamingTTSEngine):
    """Streams PCM16 16kHz audio from ElevenLabs."""

    def __init__(
        self,
        *,
        api_key: str,
        voice_id: str,
        model: str | None = None,
        frame_bytes: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model = model or settings.ELEVENLABS_MODEL
        self._frame_bytes = frame_bytes or settings.VOICE_PCM_FRAME_BYTES
        self._last_metrics = TTSAudioMetrics()

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": self._api_key},
            )
            response.raise_for_status()

    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        start = time.monotonic()
        first_audio_time: float | None = None
        frame_count = 0
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}/stream"
            f"?output_format=pcm_16000&optimize_streaming_latency=3"
        )
        payload = {"text": text, "model_id": self._model}
        buffer = bytearray()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers={"xi-api-key": self._api_key, "Content-Type": "application/json"},
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        if not chunk:
                            continue
                        buffer.extend(chunk)
                        frames, buffer = chunk_pcm_bytes(bytes(buffer), self._frame_bytes)
                        buffer = bytearray(buffer)
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
                "ElevenLabs TTS cancelled",
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
