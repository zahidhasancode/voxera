"""Amazon Polly streaming TTS engine."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import AsyncIterator

from app.core.config import settings
from app.core.logger import get_logger
from app.tts.streaming_engine import StreamingTTSEngine, TTSAudioMetrics

logger = get_logger(__name__)

_DONE = object()


class PollyStreamingTTSEngine(StreamingTTSEngine):
    """Synthesizes speech with Amazon Polly and yields PCM16 mono frames.

    Polly returns raw 16-bit little-endian PCM at the requested sample rate (8 or 16 kHz),
    so no resampling is needed. The audio body is read on a worker thread in frame-sized
    chunks, so playback can start before the whole sentence has been downloaded.
    """

    def __init__(
        self,
        *,
        voice_id: str | None = None,
        engine: str | None = None,
        region: str | None = None,
        sample_rate: int | None = None,
        frame_ms: int | None = None,
        client=None,
    ) -> None:
        self._voice_id = voice_id or settings.POLLY_VOICE_ID
        self._engine = engine or settings.POLLY_ENGINE
        self._region = region or settings.AWS_VOICE_REGION
        self._sample_rate = sample_rate or settings.VOICE_SAMPLE_RATE
        if self._sample_rate not in (8000, 16000):
            raise ValueError("Polly PCM output supports 8000 or 16000 Hz")
        frame_ms = frame_ms or settings.VOICE_FRAME_MS
        self._frame_bytes = int(self._sample_rate * frame_ms / 1000) * 2
        self._client = client
        self._last_metrics = TTSAudioMetrics()

    def _polly(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("polly", region_name=self._region)
        return self._client

    async def validate_connection(self) -> None:
        await asyncio.to_thread(self._polly().describe_voices, Engine=self._engine, LanguageCode="en-US")

    async def stream(self, text: str, *, utterance_id: str) -> AsyncIterator[bytes]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()
        frame_bytes = self._frame_bytes

        def worker() -> None:
            try:
                response = self._polly().synthesize_speech(
                    Text=text,
                    VoiceId=self._voice_id,
                    Engine=self._engine,
                    OutputFormat="pcm",
                    SampleRate=str(self._sample_rate),
                )
                body = response["AudioStream"]
                pending = b""
                while not stop.is_set():
                    chunk = body.read(frame_bytes * 5)
                    if not chunk:
                        break
                    pending += chunk
                    while len(pending) >= frame_bytes:
                        loop.call_soon_threadsafe(queue.put_nowait, pending[:frame_bytes])
                        pending = pending[frame_bytes:]
                if pending and not stop.is_set():
                    loop.call_soon_threadsafe(queue.put_nowait, pending.ljust(frame_bytes, b"\x00"))
                body.close()
            except Exception as exc:  # surfaced to the consumer below
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _DONE)

        start = time.monotonic()
        first_audio_time: float | None = None
        frames = 0
        threading.Thread(target=worker, daemon=True).start()
        try:
            while True:
                item = await queue.get()
                if item is _DONE:
                    break
                if isinstance(item, Exception):
                    raise item
                if first_audio_time is None:
                    first_audio_time = time.monotonic()
                frames += 1
                yield item
        except asyncio.CancelledError:
            logger.info("Polly TTS stream cancelled", extra_fields={"utterance_id": utterance_id, "frames_emitted": frames})
            raise
        finally:
            stop.set()
            end = time.monotonic()
            total_ms = (end - start) * 1000.0
            self._last_metrics = TTSAudioMetrics(
                time_to_first_audio_ms=(first_audio_time - start) * 1000.0 if first_audio_time else 0.0,
                total_audio_ms=total_ms,
                frame_count=frames,
                frames_per_second=frames / (total_ms / 1000.0) if total_ms > 0 else 0.0,
            )

    def last_metrics(self) -> TTSAudioMetrics:
        return self._last_metrics
