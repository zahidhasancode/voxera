"""TTS consumer: speaks text segments as they arrive and paces audio in real time.

- begin(utterance_id) opens a reply; speak(text) queues a segment (one sentence
  at a time, straight from the LLM stream); finish() says no more text is coming.
- Audio frames are sent at most `max_lead_seconds` ahead of real time. The
  provider usually returns audio much faster than it plays, and without pacing
  the client would hold seconds of buffered speech that a barge-in could not
  take back.
- The reply stays "active" until the audio that was sent has had time to play,
  so the conversation state says "system speaking" for as long as the user can
  actually hear it.
- stop() cancels at once and tells the client to drop what it has buffered.
"""

import asyncio
import time
from typing import Awaitable, Callable, Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.tts.streaming_engine import StreamingTTSEngine
from app.voice.audio import pcm16_duration_seconds

logger = get_logger(__name__)

TTS_START = "tts_start"
TTS_END = "tts_end"
TTS_CLEAR = "tts_clear"
TTS_METRICS = "tts_metrics"

FirstAudioCallback = Callable[[str], None]
PlaybackEndCallback = Callable[[str, bool], Awaitable[None]]


class TTSConsumer:
    """Streams synthesized speech for one reply at a time."""

    def __init__(
        self,
        engine: StreamingTTSEngine,
        send_bytes: Callable[[bytes], Awaitable[None]],
        send_json: Callable[[dict], Awaitable[None]],
        *,
        conversation_id: str = "",
        sample_rate: Optional[int] = None,
        max_lead_seconds: float = 0.25,
        on_first_audio: Optional[FirstAudioCallback] = None,
        on_playback_end: Optional[PlaybackEndCallback] = None,
    ):
        """Initialize consumer.

        Args:
            engine: Streaming TTS engine (mock or real).
            send_bytes: Async callback to send raw PCM16 audio to the client.
            send_json: Async callback to send JSON events to the client.
            conversation_id: Conversation ID for logging.
            sample_rate: PCM sample rate of the engine output (default: VOICE_SAMPLE_RATE).
            max_lead_seconds: How far ahead of real-time playback audio may be sent.
            on_first_audio: Called with the utterance ID when the first frame is sent.
            on_playback_end: Awaited with (utterance_id, interrupted) when the reply ends.
        """
        self.engine = engine
        self.send_bytes = send_bytes
        self.send_json = send_json
        self.conversation_id = conversation_id or ""
        self._sample_rate = sample_rate or settings.VOICE_SAMPLE_RATE
        self._max_lead = max(0.0, max_lead_seconds)
        self._on_first_audio = on_first_audio
        self._on_playback_end = on_playback_end
        self._task: Optional[asyncio.Task] = None
        self._queue: Optional[asyncio.Queue[Optional[str]]] = None
        self._utterance_id: Optional[str] = None
        self._audio_sent = False
        self._playback_cursor = 0.0  # monotonic time at which the audio sent so far finishes playing

    @property
    def is_active(self) -> bool:
        """True while a reply is being synthesized or is still playing."""
        return self._task is not None and not self._task.done()

    @property
    def current_utterance_id(self) -> Optional[str]:
        return self._utterance_id if self.is_active else None

    async def begin(self, utterance_id: str) -> None:
        """Open a new reply. Any reply still in progress is stopped first."""
        await self.stop(reason="superseded")
        self._utterance_id = utterance_id
        self._audio_sent = False
        self._playback_cursor = 0.0
        self._queue = asyncio.Queue()
        self._task = asyncio.create_task(self._run(utterance_id, self._queue))

    async def speak(self, text: str) -> None:
        """Queue one text segment of the current reply."""
        if self._queue is not None and self.is_active and text.strip():
            self._queue.put_nowait(text)

    async def finish(self) -> None:
        """Signal that the current reply has no more text."""
        if self._queue is not None and self.is_active:
            self._queue.put_nowait(None)

    async def start_speaking(self, text: str, utterance_id: str) -> None:
        """Speak one complete text (begin + speak + finish)."""
        await self.begin(utterance_id)
        await self.speak(text)
        await self.finish()

    async def stop(self, *, reason: str = "barge_in") -> bool:
        """Stop the current reply immediately.

        Returns True if a reply was in progress. If audio had already been
        sent, the client is told to discard what it has not played yet.
        """
        task = self._task
        if task is None or task.done():
            return False
        utterance_id = self._utterance_id
        had_audio = self._audio_sent
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        if had_audio:
            await self._safe_send_json({"type": TTS_CLEAR, "utterance_id": utterance_id, "reason": reason})
        logger.debug(
            "TTS stopped",
            extra_fields={"conversation_id": self.conversation_id, "utterance_id": utterance_id, "reason": reason},
        )
        return True

    async def _safe_send_json(self, payload: dict) -> None:
        try:
            await self.send_json(payload)
        except Exception:  # the socket may already be closed
            pass

    async def _run(self, utterance_id: str, queue: "asyncio.Queue[Optional[str]]") -> None:
        started = time.monotonic()
        frames = 0
        audio_bytes = 0
        segments = 0
        first_audio_ms: Optional[float] = None
        interrupted = False
        try:
            while True:
                text = await queue.get()
                if text is None:
                    break
                segments += 1
                async for frame in self.engine.stream(text, utterance_id=utterance_id):
                    if not frame:
                        continue
                    now = time.monotonic()
                    if frames == 0:
                        first_audio_ms = (now - started) * 1000.0
                        self._playback_cursor = now
                        await self.send_json({"type": TTS_START, "utterance_id": utterance_id})
                        if self._on_first_audio:
                            self._on_first_audio(utterance_id)
                    await self.send_bytes(frame)
                    self._audio_sent = True
                    frames += 1
                    audio_bytes += len(frame)
                    # If synthesis fell behind playback, the client's buffer ran dry: restart from now.
                    self._playback_cursor = max(self._playback_cursor, now) + pcm16_duration_seconds(
                        len(frame), self._sample_rate
                    )
                    lead = self._playback_cursor - time.monotonic()
                    if lead > self._max_lead:
                        await asyncio.sleep(lead - self._max_lead)
            # Everything is sent; stay active until the client has had time to play it.
            remaining = self._playback_cursor - time.monotonic()
            if frames and remaining > 0:
                await asyncio.sleep(remaining)
            if frames:
                await self.send_json({"type": TTS_END, "utterance_id": utterance_id})
            logger.info(
                "TTS reply completed",
                extra_fields={
                    "conversation_id": self.conversation_id,
                    "utterance_id": utterance_id,
                    "frames_sent": frames,
                    "segments": segments,
                },
            )
        except asyncio.CancelledError:
            interrupted = True
            logger.info(
                "TTS reply cancelled",
                extra_fields={
                    "conversation_id": self.conversation_id,
                    "utterance_id": utterance_id,
                    "frames_sent": frames,
                },
            )
        except Exception as exc:
            interrupted = True
            logger.error(
                "TTS reply failed",
                extra_fields={"conversation_id": self.conversation_id, "utterance_id": utterance_id, "error": str(exc)},
                exc_info=True,
            )
            await self._safe_send_json({"type": "error", "code": "tts_failed", "message": "Speech synthesis failed"})
        finally:
            await self._safe_send_json({
                "type": TTS_METRICS,
                "utterance_id": utterance_id,
                "conversation_id": self.conversation_id,
                "metrics": {
                    "time_to_first_audio_ms": round(first_audio_ms, 2) if first_audio_ms is not None else None,
                    "frame_count": frames,
                    "segments": segments,
                    "audio_ms": round(pcm16_duration_seconds(audio_bytes, self._sample_rate) * 1000.0, 1),
                    "interrupted": interrupted,
                },
            })
            if self._on_playback_end:
                try:
                    await self._on_playback_end(utterance_id, interrupted)
                except Exception:
                    logger.error("TTS playback-end callback failed", exc_info=True)
