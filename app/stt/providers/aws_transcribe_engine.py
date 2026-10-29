"""Amazon Transcribe streaming STT engine."""

from __future__ import annotations

import asyncio
import uuid
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.stt.engine import StreamingSTTEngine
from app.stt.models import TranscriptEvent, TranscriptType

logger = get_logger(__name__)


class AmazonTranscribeSTTEngine(StreamingSTTEngine):
    """Streams PCM16 frames to Amazon Transcribe and turns its results into transcript events.

    Transcribe sends partial results while the person speaks and a non-partial result
    for each finished segment. A segment is finished when Transcribe hears a pause, so a
    non-partial result is treated as the end of the user's turn. Credentials come from the
    standard AWS chain (environment, AWS_PROFILE, instance role).
    """

    def __init__(
        self,
        *,
        region: str | None = None,
        language: str | None = None,
        sample_rate: int | None = None,
        client_factory=None,
    ) -> None:
        self._region = region or settings.AWS_VOICE_REGION
        self._language = language or settings.AWS_TRANSCRIBE_LANGUAGE
        self._sample_rate = sample_rate or settings.VOICE_SAMPLE_RATE
        self._client_factory = client_factory or self._default_client
        self._stream = None
        self._receiver_task: asyncio.Task | None = None
        self._event_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._utterance_id: str | None = None
        self._lock = asyncio.Lock()

    def _default_client(self):
        from amazon_transcribe.client import TranscribeStreamingClient

        return TranscribeStreamingClient(region=self._region)

    async def validate_connection(self) -> None:
        await self._connect()
        await self.close()

    async def process_audio(self, frame: bytes) -> Optional[TranscriptEvent]:
        await self._connect()
        if self._utterance_id is None:
            self._utterance_id = str(uuid.uuid4())
        await self._stream.input_stream.send_audio_event(audio_chunk=frame)
        return self._dequeue_event()

    async def finalize_utterance(self) -> Optional[TranscriptEvent]:
        if self._stream is not None:
            try:
                await self._stream.input_stream.end_stream()
            except Exception as exc:
                logger.warning("Transcribe end_stream failed", extra_fields={"error": repr(exc)})
        deadline = asyncio.get_running_loop().time() + 2.0
        final_event: TranscriptEvent | None = None
        while asyncio.get_running_loop().time() < deadline:
            event = self._dequeue_event()
            if event is None:
                if self._receiver_task is not None and self._receiver_task.done():
                    break
                await asyncio.sleep(0.05)
                continue
            final_event = event
            if event.type == TranscriptType.FINAL:
                break
        await self.reset()
        return final_event

    async def reset(self) -> None:
        self._utterance_id = None
        while not self._event_queue.empty():
            self._event_queue.get_nowait()
        await self.close()

    async def close(self) -> None:
        async with self._lock:
            if self._stream is not None:
                try:
                    await self._stream.input_stream.end_stream()
                except Exception as exc:  # the stream may already be closed
                    logger.debug("Transcribe stream close failed", extra_fields={"error": repr(exc)})
            if self._receiver_task and not self._receiver_task.done():
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass
            self._receiver_task = None
            self._stream = None

    async def _connect(self) -> None:
        if self._stream is not None:
            return
        async with self._lock:
            if self._stream is not None:
                return
            client = self._client_factory()
            self._stream = await client.start_stream_transcription(
                language_code=self._language,
                media_sample_rate_hz=self._sample_rate,
                media_encoding="pcm",
            )
            self._receiver_task = asyncio.create_task(self._receive_loop(self._stream))
            logger.info("Amazon Transcribe connected", extra_fields={"region": self._region})

    async def _receive_loop(self, stream) -> None:
        try:
            async for event in stream.output_stream:
                for parsed in self.parse_results(getattr(event, "transcript", None)):
                    await self._event_queue.put(parsed)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Transcribe receive loop failed", extra_fields={"error": repr(exc)})

    def parse_results(self, transcript) -> list[TranscriptEvent]:
        """Turn one Transcribe transcript message into transcript events."""
        out: list[TranscriptEvent] = []
        for result in getattr(transcript, "results", None) or []:
            alternatives = getattr(result, "alternatives", None) or []
            if not alternatives:
                continue
            text = (getattr(alternatives[0], "transcript", "") or "").strip()
            if not text:
                continue
            utterance_id = self._utterance_id or str(uuid.uuid4())
            if getattr(result, "is_partial", True):
                out.append(TranscriptEvent(type=TranscriptType.PARTIAL, utterance_id=utterance_id, transcript=text, confidence=0.5))
            else:
                out.append(TranscriptEvent(type=TranscriptType.FINAL, utterance_id=utterance_id, transcript=text, confidence=1.0))
                self._utterance_id = None  # the next utterance gets a new ID
        return out

    def _dequeue_event(self) -> TranscriptEvent | None:
        try:
            return self._event_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
