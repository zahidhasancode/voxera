"""Deepgram live streaming STT engine."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional
from urllib.parse import urlencode

import websockets

from app.core.config import settings
from app.core.logger import get_logger
from app.stt.engine import StreamingSTTEngine
from app.stt.models import TranscriptEvent, TranscriptType

logger = get_logger(__name__)


class DeepgramStreamingSTTEngine(StreamingSTTEngine):
    """Streams PCM16 frames to Deepgram live transcription WebSocket."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model or settings.DEEPGRAM_MODEL
        self._language = language or settings.DEEPGRAM_LANGUAGE
        self._sample_rate = sample_rate or settings.VOICE_SAMPLE_RATE
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._receiver_task: asyncio.Task | None = None
        self._event_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._utterance_id: str | None = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def validate_connection(self) -> None:
        await self._connect()
        await self.close()

    async def process_audio(self, frame: bytes) -> Optional[TranscriptEvent]:
        await self._connect()
        if self._utterance_id is None:
            self._utterance_id = str(uuid.uuid4())
        if self._ws is not None:
            await self._ws.send(frame)
        return await self._dequeue_event()

    async def finalize_utterance(self) -> Optional[TranscriptEvent]:
        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "Finalize"}))
            except Exception as exc:
                logger.warning("Deepgram finalize failed", extra_fields={"error": str(exc)})
        deadline = asyncio.get_event_loop().time() + 2.0
        final_event: TranscriptEvent | None = None
        while asyncio.get_event_loop().time() < deadline:
            event = await self._dequeue_event()
            if event is None:
                await asyncio.sleep(0.05)
                continue
            if event.type == TranscriptType.FINAL:
                final_event = event
                break
            final_event = event
        await self.reset()
        return final_event

    async def reset(self) -> None:
        self._utterance_id = None
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        await self.close()

    async def close(self) -> None:
        async with self._lock:
            if self._receiver_task and not self._receiver_task.done():
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass
            self._receiver_task = None
            if self._ws is not None:
                try:
                    await self._ws.close()
                except Exception:
                    pass
            self._ws = None
            self._connected = False

    async def _connect(self) -> None:
        if self._connected and self._ws is not None:
            return
        async with self._lock:
            if self._connected and self._ws is not None:
                return
            params = urlencode(
                {
                    "model": self._model,
                    "language": self._language,
                    "encoding": "linear16",
                    "sample_rate": str(self._sample_rate),
                    "channels": "1",
                    "interim_results": "true",
                    "punctuate": "true",
                    "endpointing": "300",
                }
            )
            url = f"wss://api.deepgram.com/v1/listen?{params}"
            self._ws = await websockets.connect(
                url,
                extra_headers={"Authorization": f"Token {self._api_key}"},
                ping_interval=20,
                ping_timeout=10,
                open_timeout=10,
            )
            self._connected = True
            self._receiver_task = asyncio.create_task(self._receive_loop())
            logger.info("Deepgram STT connected", extra_fields={"model": self._model})

    async def _receive_loop(self) -> None:
        assert self._ws is not None
        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    continue
                payload = json.loads(message)
                event = self._parse_result(payload)
                if event is not None:
                    await self._event_queue.put(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Deepgram receive loop failed", extra_fields={"error": str(exc)})

    def _parse_result(self, payload: dict) -> TranscriptEvent | None:
        channel = payload.get("channel") or {}
        alternatives = channel.get("alternatives") or []
        if not alternatives:
            return None
        transcript = (alternatives[0].get("transcript") or "").strip()
        if not transcript:
            return None
        is_final = bool(payload.get("is_final") or payload.get("speech_final"))
        utterance_id = self._utterance_id or str(uuid.uuid4())
        confidence = float(alternatives[0].get("confidence") or 0.0)
        return TranscriptEvent(
            type=TranscriptType.FINAL if is_final else TranscriptType.PARTIAL,
            utterance_id=utterance_id,
            transcript=transcript,
            confidence=confidence,
        )

    async def _dequeue_event(self) -> TranscriptEvent | None:
        try:
            return self._event_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
