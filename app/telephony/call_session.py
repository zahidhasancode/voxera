"""Twilio call session with a proper state machine.

CallSession owns call_sid, stream_sid, conversation_id, state enum,
and references to STT, LLM consumer, and TTS consumer. State transitions
are async-safe and prevent race conditions (single active TTS, cancel LLM
on interruption, stop TTS immediately on user speech).

Barge-in: detect user audio while SPEAKING, mute outbound immediately,
cancel LLM and stop TTS, transition INTERRUPTED → LISTENING. No residual
audio sent. Optional early VAD for <150ms latency.

Telephony hot path is intended to be non-blocking: no time.sleep or
blocking I/O on the event loop; use async APIs or run_blocking in executor.
"""

import asyncio
import struct
import time
from enum import Enum
from typing import Awaitable, Callable, Optional
from uuid import UUID, uuid4

from app.telephony.call_metrics import CallPerformanceMetrics
from app.telephony.telephony_log import (
    log_telephony,
    EVENT_CALL_ENDED,
    EVENT_CALL_STARTED,
    EVENT_ERROR,
    EVENT_FIRST_AUDIO_SENT,
    EVENT_FIRST_TOKEN,
    EVENT_FIRST_USER_AUDIO,
    EVENT_INTERRUPTION,
    EVENT_LLM_STARTED,
    EVENT_TRANSCRIPT_RECEIVED,
    EVENT_TTS_STARTED,
)

from app.conversation.events import UserInterrupted, UserTurnCompleted, UserTurnStarted
from app.conversation.state import ConversationState
from app.conversation.turn_manager import TurnManager
from app.core.logger import get_logger
from app.llm.llm_consumer import LLMConsumer
from app.llm.streaming_engine import MockStreamingLLMEngine
from app.stt.engine import MockSTTEngine, StreamingSTTEngine
from app.stt.consumer import STTConsumer
from app.stt.models import TranscriptEvent
from app.telephony.audio_convert import convert_twilio_audio, pcm16_16k_to_twilio_audio
from app.telephony.twilio_stream import build_twilio_media_message
from app.tts import MockStreamingTTSEngine, TTSConsumer

logger = get_logger(__name__)

# 20 ms at 16 kHz, PCM16 = 320 samples * 2 bytes
PCM_FRAME_BYTES = 640

# Barge-in: emit partial every 1 frame (~20ms) for low latency
BARGE_IN_PARTIAL_INTERVAL = 1
# VAD: mean absolute sample value above this triggers early barge-in (PCM16 range 0–32767)
BARGE_IN_ENERGY_THRESHOLD = 400

# Error recovery: fallback TTS and LLM timeout
FALLBACK_TTS_MESSAGE = "Sorry, I'm having trouble right now. Let me transfer you."
LLM_TIMEOUT_SECONDS = 8.0

# Silence detection: prompt after 8s, hang up 8s after prompt if still silent
SILENCE_PROMPT_SECONDS = 8.0
SILENCE_HANGUP_AFTER_PROMPT_SECONDS = 8.0
SILENCE_CHECK_INTERVAL_SECONDS = 1.0
SILENCE_PROMPT_MESSAGE = "Are you still there?"


class CallSessionState(Enum):
    """Call session state for Twilio Media Streams."""

    CONNECTING = "connecting"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    ENDED = "ended"


# Allowed (from_state, to_state) transitions
_VALID_TRANSITIONS: set[tuple[CallSessionState, CallSessionState]] = {
    (CallSessionState.CONNECTING, CallSessionState.LISTENING),
    (CallSessionState.LISTENING, CallSessionState.PROCESSING),
    (CallSessionState.PROCESSING, CallSessionState.SPEAKING),
    (CallSessionState.SPEAKING, CallSessionState.INTERRUPTED),
    (CallSessionState.INTERRUPTED, CallSessionState.LISTENING),
}
for s in CallSessionState:
    if s != CallSessionState.ENDED:
        _VALID_TRANSITIONS.add((s, CallSessionState.ENDED))


class CallSession:
    """Per-call session with state machine, STT, LLM, and TTS.

    State flow: CONNECTING → LISTENING → PROCESSING → SPEAKING;
    on barge-in: SPEAKING → INTERRUPTED → LISTENING; any → ENDED on stop.
    All transitions and consumer actions are guarded by an async lock.
    """

    def __init__(self, call_sid: str, stream_sid: str) -> None:
        self.call_sid = call_sid
        self.stream_sid = stream_sid
        self.conversation_state = ConversationState()
        self.conversation_id: UUID = self.conversation_state.conversation_id

        self._state = CallSessionState.CONNECTING
        self._lock = asyncio.Lock()
        self._pcm_buffer: bytearray = bytearray()
        self._send_text: Optional[Callable[[str], Awaitable[None]]] = None
        # Mute outbound as soon as barge-in is detected so no residual TTS is sent
        self._outbound_muted = False

        # Performance metrics (measurement hooks only)
        self.metrics = CallPerformanceMetrics(
            call_sid=call_sid,
            call_start_time=0.0,  # set in start() when Twilio "start" is processed
        )
        # Silence detection: background task and state
        self._last_user_audio_time: float = 0.0
        self._silence_prompt_played: bool = False
        self._silence_prompt_time: Optional[float] = None
        self._silence_task: Optional[asyncio.Task] = None
        self._on_silence_hangup: Optional[Callable[[], Awaitable[None]]] = None
        # References (set in start())
        self.turn_manager: Optional[TurnManager] = None
        self.stt_engine: Optional[StreamingSTTEngine] = None
        self.stt_consumer: Optional[STTConsumer] = None
        self.llm_consumer: Optional[LLMConsumer] = None
        self.tts_consumer: Optional[TTSConsumer] = None

    @property
    def state(self) -> CallSessionState:
        """Current session state. For decisions that depend on state, hold _lock and read _state (or use a snapshot taken under _lock) to avoid races with stop() or other transitions."""
        return self._state

    def _apply_transition(self, new_state: CallSessionState) -> bool:
        """Apply transition if allowed. All state transitions are under _lock and are atomic. Caller must hold _lock. Returns True if transitioned."""
        if self._state == CallSessionState.ENDED:
            return False
        if (self._state, new_state) not in _VALID_TRANSITIONS:
            log_telephony(
                EVENT_ERROR,
                call_sid=self.call_sid,
                stream_sid=self.stream_sid,
                conversation_id=str(self.conversation_id),
                state=self._state.value,
                level="warning",
                component="state",
                reason="invalid_transition",
                from_state=self._state.value,
                to_state=new_state.value,
            )
            return False
        old = self._state
        self._state = new_state
        return True

    async def transition_to(self, new_state: CallSessionState) -> bool:
        """Transition to new_state if allowed. Async-safe. Returns True if transitioned."""
        async with self._lock:
            return self._apply_transition(new_state)

    async def start(
        self,
        *,
        send_text: Optional[Callable[[str], Awaitable[None]]] = None,
        send_json: Optional[Callable[[dict], Awaitable[None]]] = None,
        on_silence_hangup: Optional[Callable[[], Awaitable[None]]] = None,
    ) -> None:
        """Create STT, turn manager, LLM, TTS and move to LISTENING. Async-safe."""
        if send_text is None:
            send_text = _noop_send_text
        if send_json is None:
            send_json = _noop_send_json

        self.metrics.call_start_time = time.monotonic()
        self._send_text = send_text
        self._last_user_audio_time = time.monotonic()
        self._silence_prompt_played = False
        self._silence_prompt_time = None
        self._on_silence_hangup = on_silence_hangup

        async def _send_json_with_first_token(payload: dict) -> None:
            if payload.get("type") == "llm_partial" and self.metrics.first_token_time is None:
                self.metrics.first_token_time = time.monotonic()
                log_telephony(
                    EVENT_FIRST_TOKEN,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=self._state.value,
                    metrics=self.metrics.to_log_dict(),
                )
            await send_json(payload)

        self.turn_manager = TurnManager(
            state=self.conversation_state,
            on_user_turn_started=self._on_user_turn_started,
            on_user_turn_completed=self._on_user_turn_completed,
            on_user_interrupted=self._on_user_interrupted,
        )
        self.stt_engine = MockSTTEngine(
            partial_interval=BARGE_IN_PARTIAL_INTERVAL,
            word_probability=0.25,
            silence_threshold=15,
        )
        self.stt_consumer = STTConsumer(
            engine=self.stt_engine,
            transcript_callback=self._transcript_callback,
            max_queue_size=50,
            error_callback=self._on_stt_error,
        )

        llm_engine = MockStreamingLLMEngine(min_token_delay_ms=20.0, max_token_delay_ms=40.0)
        self.llm_consumer = LLMConsumer(
            engine=llm_engine,
            send_json=_send_json_with_first_token,
            conversation_id=str(self.conversation_id),
        )
        tts_engine = MockStreamingTTSEngine()
        self.tts_consumer = TTSConsumer(
            engine=tts_engine,
            send_bytes=self.send_audio_frame,
            send_json=send_json,
            conversation_id=str(self.conversation_id),
        )

        await self.stt_consumer.start()
        await self.transition_to(CallSessionState.LISTENING)
        self._silence_task = asyncio.create_task(self._silence_loop())
        log_telephony(
            EVENT_CALL_STARTED,
            call_sid=self.call_sid,
            stream_sid=self.stream_sid,
            conversation_id=str(self.conversation_id),
            state=self._state.value,
        )

    async def _transcript_callback(self, event: TranscriptEvent) -> None:
        try:
            if self.metrics.first_transcript_time is None:
                self.metrics.first_transcript_time = time.monotonic()
                log_telephony(
                    EVENT_TRANSCRIPT_RECEIVED,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=self._state.value,
                    metrics=self.metrics.to_log_dict(),
                )
            if not self.turn_manager:
                return
            await self.turn_manager.process_transcript_event(event)
        except Exception as e:
            await self._handle_pipeline_error("stt", e)

    async def _on_user_turn_started(self, _event: UserTurnStarted) -> None:
        async with self._lock:
            if self._state == CallSessionState.ENDED:
                return
            if self.llm_consumer:
                self.llm_consumer.cancel()
            if self._state == CallSessionState.PROCESSING:
                self._apply_transition(CallSessionState.LISTENING)

    async def _on_user_turn_completed(self, event: UserTurnCompleted) -> None:
        async with self._lock:
            if self._state != CallSessionState.LISTENING:
                return
            if not self._apply_transition(CallSessionState.PROCESSING):
                return
            llm = self.llm_consumer
            tts = self.tts_consumer
        if not llm or not tts:
            return
        async def _run_llm_with_timeout() -> None:
            try:
                await asyncio.wait_for(
                    llm.start_generation(
                        transcript=event.transcript,
                        utterance_id=event.utterance_id,
                        on_system_turn_start=self._on_system_turn_start,
                        on_system_turn_end=self._on_system_turn_end,
                        on_llm_final=self._on_llm_final,
                    ),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError as e:
                log_telephony(
                    EVENT_ERROR,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=self._state.value,
                    metrics=self.metrics.to_log_dict(),
                    level="warning",
                    component="llm",
                    error_type="TimeoutError",
                    error=str(e),
                    timeout_seconds=LLM_TIMEOUT_SECONDS,
                )
                await self._handle_pipeline_error("llm", e)
        asyncio.create_task(_run_llm_with_timeout())
        log_telephony(
            EVENT_LLM_STARTED,
            call_sid=self.call_sid,
            stream_sid=self.stream_sid,
            conversation_id=str(self.conversation_id),
            state=self._state.value,
            utterance_id=event.utterance_id,
            transcript_length=len(event.transcript),
        )

    async def _on_system_turn_start(self) -> None:
        async with self._lock:
            if self._state == CallSessionState.ENDED:
                return
            if self.tts_consumer:
                await self.tts_consumer.stop()
            self.conversation_state.start_system_turn()

    async def _on_system_turn_end(self) -> None:
        self.conversation_state.complete_system_turn()

    async def _on_llm_final(self, text: str, utterance_id: str) -> None:
        try:
            async with self._lock:
                if self._state == CallSessionState.ENDED:
                    return
                if self._state != CallSessionState.PROCESSING and self._state != CallSessionState.SPEAKING:
                    return
                self._apply_transition(CallSessionState.SPEAKING)
                tts = self.tts_consumer
            if tts:
                await tts.start_speaking(text=text, utterance_id=utterance_id)
                log_telephony(
                    EVENT_TTS_STARTED,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=self._state.value,
                    utterance_id=utterance_id,
                )
        except Exception as e:
            await self._handle_pipeline_error("tts", e)

    async def _on_user_interrupted(self, _event: UserInterrupted) -> None:
        """Called by TurnManager when STT partial arrives while system is speaking."""
        await self._handle_barge_in()

    def _on_stt_error(self, _component: str, error: BaseException) -> None:
        """Sync callback for STT consumer errors; schedule async recovery."""
        asyncio.create_task(self._handle_pipeline_error("stt", error))

    async def _handle_pipeline_error(self, component: str, error: BaseException) -> None:
        """On pipeline failure: log, stop LLM/TTS, transition to LISTENING, play fallback TTS.

        Never raises; ensures no silent failure. WebSocket remains alive.
        """
        log_telephony(
            EVENT_ERROR,
            call_sid=self.call_sid,
            stream_sid=self.stream_sid,
            conversation_id=str(self.conversation_id),
            state=self._state.value,
            metrics=self.metrics.to_log_dict(),
            level="error",
            component=component,
            error_type=type(error).__name__,
            error=str(error),
            exc_info=True,
        )
        try:
            async with self._lock:
                if self._state == CallSessionState.ENDED:
                    return
                if self.llm_consumer:
                    self.llm_consumer.cancel()
                if self.tts_consumer:
                    await self.tts_consumer.stop()
                if self._state in (CallSessionState.PROCESSING, CallSessionState.SPEAKING):
                    self._apply_transition(CallSessionState.INTERRUPTED)
                    self._apply_transition(CallSessionState.LISTENING)
                self.conversation_state.interrupt_user()
                self.conversation_state.complete_system_turn()
            await self._play_fallback_tts()
        except Exception as e:
            log_telephony(
                EVENT_ERROR,
                call_sid=self.call_sid,
                stream_sid=self.stream_sid,
                conversation_id=str(self.conversation_id),
                state=self._state.value,
                level="error",
                component=component,
                error_type="recovery",
                error=str(e),
                exc_info=True,
            )

    async def _play_fallback_tts(self) -> None:
        """Play fallback TTS message. Never raises. Ensures only one TTS stream: stop current then start."""
        try:
            async with self._lock:
                if self._state == CallSessionState.ENDED or not self.tts_consumer:
                    return
                await self.tts_consumer.stop()
                tts = self.tts_consumer
            await tts.start_speaking(
                text=FALLBACK_TTS_MESSAGE,
                utterance_id=f"fallback-{uuid4()}",
            )
        except Exception as e:
            log_telephony(
                EVENT_ERROR,
                call_sid=self.call_sid,
                stream_sid=self.stream_sid,
                conversation_id=str(self.conversation_id),
                state=self._state.value,
                level="error",
                component="fallback_tts",
                error=str(e),
                exc_info=True,
            )

    async def _handle_barge_in(self) -> None:
        """Execute barge-in: mute outbound immediately, cancel LLM, stop TTS, reset STT, transition.

        Idempotent: safe to call from VAD or STT path; only acts when state is SPEAKING or PROCESSING.
        Ensures no residual buffered TTS is sent (mute set first).
        """
        async with self._lock:
            if self._state == CallSessionState.ENDED:
                return
            if self._state != CallSessionState.SPEAKING and self._state != CallSessionState.PROCESSING:
                return
            # 1. Mute outbound first so in-flight send_audio_frame calls drop frames immediately
            self._outbound_muted = True
            # 2. Cancel LLM so no more tokens push to TTS
            if self.llm_consumer:
                self.llm_consumer.cancel()
            # 3. Stop TTS stream (cancels task; any send_audio_frame after mute no-ops)
            if self.tts_consumer:
                await self.tts_consumer.stop()
            # 4. Keep conversation state in sync (barge-in semantics)
            self.conversation_state.interrupt_user()
            self.conversation_state.complete_system_turn()
            # 5. Reset STT for clean next utterance
            if self.stt_engine:
                await self.stt_engine.reset()
            # 6. Transition INTERRUPTED → LISTENING
            self._apply_transition(CallSessionState.INTERRUPTED)
            self._apply_transition(CallSessionState.LISTENING)
            # 7. Unmute for next TTS
            self._outbound_muted = False
        log_telephony(
            EVENT_INTERRUPTION,
            call_sid=self.call_sid,
            stream_sid=self.stream_sid,
            conversation_id=str(self.conversation_id),
            state=self._state.value,
        )

    async def _request_barge_in(self) -> None:
        """Request barge-in (e.g. from early VAD). Safe to call; no-op if not SPEAKING/PROCESSING."""
        await self._handle_barge_in()

    async def _silence_loop(self) -> None:
        """Lightweight background task: after 8s silence play prompt; after 8s more, end call."""
        try:
            while True:
                await asyncio.sleep(SILENCE_CHECK_INTERVAL_SECONDS)
                async with self._lock:
                    if self._state == CallSessionState.ENDED:
                        break
                    state = self._state
                    last_audio = self._last_user_audio_time
                    prompt_played = self._silence_prompt_played
                    prompt_time = self._silence_prompt_time
                if state != CallSessionState.LISTENING:
                    continue
                now = time.monotonic()
                elapsed_since_audio = now - last_audio
                if elapsed_since_audio < SILENCE_PROMPT_SECONDS:
                    continue
                if not prompt_played:
                    async with self._lock:
                        if self._state != CallSessionState.LISTENING or self._silence_prompt_played:
                            continue
                        self._silence_prompt_played = True
                        self._silence_prompt_time = time.monotonic()
                        if self.tts_consumer:
                            await self.tts_consumer.stop()
                        tts = self.tts_consumer
                    if tts:
                        try:
                            await tts.start_speaking(
                                text=SILENCE_PROMPT_MESSAGE,
                                utterance_id=f"silence-prompt-{uuid4()}",
                            )
                        except Exception as e:
                            log_telephony(
                                EVENT_ERROR,
                                call_sid=self.call_sid,
                                stream_sid=self.stream_sid,
                                conversation_id=str(self.conversation_id),
                                state=self._state.value,
                                level="warning",
                                component="silence_prompt_tts",
                                error=str(e),
                            )
                    continue
                if prompt_time is None:
                    continue
                if (now - prompt_time) >= SILENCE_HANGUP_AFTER_PROMPT_SECONDS:
                    log_telephony(
                        "silence_hangup",
                        call_sid=self.call_sid,
                        stream_sid=self.stream_sid,
                        conversation_id=str(self.conversation_id),
                        state=self._state.value,
                        metrics=self.metrics.to_log_dict(),
                    )
                    if self._on_silence_hangup:
                        try:
                            await self._on_silence_hangup()
                        except Exception as e:
                            log_telephony(
                                EVENT_ERROR,
                                call_sid=self.call_sid,
                                stream_sid=self.stream_sid,
                                conversation_id=str(self.conversation_id),
                                state=self._state.value,
                                level="warning",
                                component="silence_hangup",
                                error=str(e),
                            )
                    break
        except asyncio.CancelledError:
            pass

    def _frame_energy(self, frame: bytes) -> float:
        """Mean absolute value of PCM16 samples (0–32767). Used for VAD."""
        if len(frame) < 2:
            return 0.0
        n = len(frame) // 2
        total = 0
        for i in range(n):
            total += abs(struct.unpack_from("<h", frame, i * 2)[0])
        return total / n if n else 0.0

    async def feed_mulaw(self, mulaw_bytes: bytes) -> None:
        """Feed decoded μ-law into STT (buffer and dispatch 20 ms frames). Non-blocking.

        When state is SPEAKING, runs early VAD on each frame; if energy exceeds threshold,
        triggers barge-in immediately for <150ms latency without waiting for STT partial.
        Shared session state (state, stt_consumer, buffer) is read/updated under _lock.
        """
        try:
            if not mulaw_bytes:
                return
            pcm = convert_twilio_audio(mulaw_bytes)
            async with self._lock:
                if self._state == CallSessionState.ENDED:
                    return
                stt = self.stt_consumer
                if not stt:
                    return
                now = time.monotonic()
                self._last_user_audio_time = now
                self._silence_prompt_played = False
                self._silence_prompt_time = None
                first_user_audio_log = self.metrics.first_user_audio_time is None
                if first_user_audio_log:
                    self.metrics.first_user_audio_time = now
                self._pcm_buffer.extend(pcm)
                frames = []
                while len(self._pcm_buffer) >= PCM_FRAME_BYTES:
                    frames.append(bytes(self._pcm_buffer[:PCM_FRAME_BYTES]))
                    del self._pcm_buffer[:PCM_FRAME_BYTES]
                state_snapshot = self._state
            if first_user_audio_log:
                log_telephony(
                    EVENT_FIRST_USER_AUDIO,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=state_snapshot.value,
                )
            for frame in frames:
                if state_snapshot == CallSessionState.SPEAKING:
                    energy = self._frame_energy(frame)
                    if energy >= BARGE_IN_ENERGY_THRESHOLD:
                        asyncio.create_task(self._request_barge_in())
                asyncio.create_task(stt.process_frame(frame))
        except Exception as e:
            await self._handle_pipeline_error("stt", e)

    async def send_audio_frame(self, pcm16_16k: bytes) -> None:
        """Send one PCM16 16 kHz frame as Twilio media event.

        No-op if ENDED, no send_text, or outbound is muted (barge-in).
        Mute is checked first so no residual buffered TTS is sent after interrupt.
        """
        if not pcm16_16k or not self._send_text:
            return
        async with self._lock:
            if self._outbound_muted or self._state == CallSessionState.ENDED:
                return
        mulaw = pcm16_16k_to_twilio_audio(pcm16_16k)
        if not mulaw:
            return
        msg = build_twilio_media_message(self.stream_sid, mulaw)
        # Check again before send so we never push a frame after barge-in muted or after call ended
        async with self._lock:
            if self._outbound_muted or self._state == CallSessionState.ENDED or self._send_text is None:
                return
            send_text = self._send_text
        if self.metrics.first_audio_response_time is None:
            self.metrics.first_audio_response_time = time.monotonic()
            log_telephony(
                EVENT_FIRST_AUDIO_SENT,
                call_sid=self.call_sid,
                stream_sid=self.stream_sid,
                conversation_id=str(self.conversation_id),
                state=self._state.value,
                metrics=self.metrics.to_log_dict(),
            )
        try:
            await send_text(msg)
        except Exception as e:
            await self._handle_pipeline_error("tts", e)

    async def stop(self) -> None:
        """Transition to ENDED, cancel all tasks, flush metrics, tear down. Idempotent. Never raises."""
        try:
            async with self._lock:
                if self._state == CallSessionState.ENDED:
                    return
                self._apply_transition(CallSessionState.ENDED)
                # Clear send path immediately so no audio frame is sent after call ended
                self._send_text = None
                self._outbound_muted = True
                self.metrics.call_end_time = time.monotonic()
                # Flush metrics immediately so they are logged even if teardown fails
                log_telephony(
                    EVENT_CALL_ENDED,
                    call_sid=self.call_sid,
                    stream_sid=self.stream_sid,
                    conversation_id=str(self.conversation_id),
                    state=self._state.value,
                    metrics=self.metrics.to_log_dict(),
                )
                # Capture silence task to await outside lock (avoid deadlock)
                silence_task = self._silence_task
                self._silence_task = None
                if self.llm_consumer:
                    self.llm_consumer.cancel()
                if self.tts_consumer:
                    await self.tts_consumer.stop()
                if self.stt_consumer:
                    await self.stt_consumer.stop()
                    self.stt_consumer = None
                self.stt_engine = None
                self.turn_manager = None
                self.llm_consumer = None
                self.tts_consumer = None
                self._on_silence_hangup = None
                self._outbound_muted = False
                self._pcm_buffer.clear()
            # Cancel and await silence task outside lock so no orphan remains
            if silence_task and not silence_task.done():
                silence_task.cancel()
                try:
                    await asyncio.wait_for(silence_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        except Exception as e:
            log_telephony(
                EVENT_ERROR,
                call_sid=self.call_sid,
                stream_sid=self.stream_sid,
                conversation_id=str(self.conversation_id),
                state=self._state.value,
                level="error",
                component="stop",
                error=str(e),
                exc_info=True,
            )


async def _noop_send_text(_msg: str) -> None:
    pass


async def _noop_send_json(_payload: dict) -> None:
    pass