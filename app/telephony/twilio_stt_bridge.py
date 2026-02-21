"""Bridge Twilio Media Streams into the existing STT and turn-taking pipeline.

Feeds decoded PCM (μ-law → PCM16 16 kHz) into the STT engine; when STT emits
TranscriptEvent, injects into TurnManager. Maintains per-call session state.
Outbound: accepts PCM16 16 kHz from TTS, converts to μ-law 8 kHz, sends as
Twilio media events for real-time streaming. Uses async throughout; supports barge-in.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from app.conversation.state import ConversationState
from app.conversation.turn_manager import TurnManager
from app.core.logger import get_logger
from app.stt.engine import MockSTTEngine, StreamingSTTEngine
from app.stt.consumer import STTConsumer
from app.stt.models import TranscriptEvent
from app.telephony.audio_convert import convert_twilio_audio, pcm16_16k_to_twilio_audio
from app.telephony.twilio_stream import build_twilio_media_message

logger = get_logger(__name__)

# 20 ms at 16 kHz, PCM16 = 320 samples * 2 bytes
PCM_FRAME_BYTES = 640


@dataclass
class TwilioCallPipeline:
    """Per-call pipeline: STT → TranscriptEvent → TurnManager; TTS → outbound media.

    Created on stream start; fed mulaw chunks from media events;
    torn down on stream stop. Maintains PCM buffer and dispatches
    20 ms frames to STT. Optional outbound: send_audio_frame() accepts
    PCM16 16 kHz and sends Twilio media events (real-time, no buffering).
    """

    stream_sid: str
    call_sid: str
    conversation_state: ConversationState = field(default_factory=ConversationState)
    turn_manager: Optional[TurnManager] = None
    stt_engine: Optional[StreamingSTTEngine] = None
    stt_consumer: Optional[STTConsumer] = None
    _pcm_buffer: bytearray = field(default_factory=bytearray, repr=False)
    _send_text: Optional[Callable[[str], Awaitable[None]]] = field(default=None, repr=False)

    async def start(
        self,
        *,
        send_text: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        """Create and start STT consumer and turn manager. Call once after stream start.

        If send_text is provided (e.g. websocket.send_text), outbound audio
        via send_audio_frame() will be sent as Twilio media events.
        """
        self._send_text = send_text
        self.turn_manager = TurnManager(
            state=self.conversation_state,
            on_user_turn_started=self._on_user_turn_started,
            on_user_turn_completed=self._on_user_turn_completed,
            on_user_interrupted=self._on_user_interrupted,
        )
        self.stt_engine = MockSTTEngine(
            partial_interval=3,
            word_probability=0.25,
            silence_threshold=15,
        )
        self.stt_consumer = STTConsumer(
            engine=self.stt_engine,
            transcript_callback=self._transcript_callback,
            max_queue_size=50,
        )
        await self.stt_consumer.start()
        logger.info(
            "Twilio call pipeline started",
            extra_fields={"stream_sid": self.stream_sid, "call_sid": self.call_sid},
        )

    async def _transcript_callback(self, event: TranscriptEvent) -> None:
        """Inject STT TranscriptEvent into turn manager (async, non-blocking)."""
        if not self.turn_manager:
            return
        await self.turn_manager.process_transcript_event(event)

    async def _on_user_turn_started(self, _event: object) -> None:
        """No-op for now; can wire LLM trigger later."""
        pass

    async def _on_user_turn_completed(self, _event: object) -> None:
        """No-op for now; can wire LLM/TTS later."""
        pass

    async def _on_user_interrupted(self, _event: object) -> None:
        """Barge-in: reset STT engine so next speech is clean."""
        if self.stt_engine:
            await self.stt_engine.reset()
            logger.debug(
                "STT engine reset on barge-in",
                extra_fields={"stream_sid": self.stream_sid},
            )

    async def feed_mulaw(self, mulaw_bytes: bytes) -> None:
        """Convert μ-law to PCM16 16 kHz, buffer, and feed 20 ms frames to STT.

        Does not block: enqueues frames via create_task so the event loop
        stays free for WebSocket receive.
        """
        if not mulaw_bytes or not self.stt_consumer:
            return
        pcm = convert_twilio_audio(mulaw_bytes)
        self._pcm_buffer.extend(pcm)
        while len(self._pcm_buffer) >= PCM_FRAME_BYTES:
            frame = bytes(self._pcm_buffer[:PCM_FRAME_BYTES])
            del self._pcm_buffer[:PCM_FRAME_BYTES]
            # Non-blocking: enqueue via task so WebSocket receive loop is not blocked
            asyncio.create_task(self.stt_consumer.process_frame(frame))

    async def send_audio_frame(self, pcm16_16k: bytes) -> None:
        """Send one PCM16 16 kHz frame to Twilio as a media event (real-time, no buffering).

        Converts to μ-law 8 kHz, base64, and sends {"event":"media","streamSid":...,"media":{"payload":...}}.
        No-op if send_text was not set at start(). Call from TTS or other PCM source.
        """
        if not pcm16_16k or not self._send_text:
            return
        mulaw = pcm16_16k_to_twilio_audio(pcm16_16k)
        if not mulaw:
            return
        msg = build_twilio_media_message(self.stream_sid, mulaw)
        await self._send_text(msg)

    async def stop(self) -> None:
        """Finalize STT and stop consumer. Call on stream stop."""
        if self.stt_consumer:
            await self.stt_consumer.stop()
            self.stt_consumer = None
        self.stt_engine = None
        self.turn_manager = None
        self._send_text = None
        self._pcm_buffer.clear()
        logger.info(
            "Twilio call pipeline stopped",
            extra_fields={"stream_sid": self.stream_sid, "call_sid": self.call_sid},
        )
