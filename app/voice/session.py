"""One voice conversation: turn-taking, LLM, speech and timing in one place.

The transport (browser WebSocket, phone bridge) feeds transcript events in and
provides two callbacks for sending JSON events and PCM16 audio out. Everything
between "the user finished a sentence" and "the reply has been heard" lives
here, so it can be tested without a network.
"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable, Optional

from app.conversation.events import UserInterrupted, UserTurnCompleted, UserTurnStarted
from app.conversation.state import ConversationState
from app.conversation.turn_manager import TurnManager
from app.core.config import settings
from app.core.logger import get_logger
from app.llm.llm_consumer import CANCELLED, LLMConsumer
from app.llm.streaming_engine import StreamingLLMEngine
from app.stt.models import TranscriptEvent, TranscriptType
from app.tts.streaming_engine import StreamingTTSEngine
from app.tts.tts_consumer import TTSConsumer
from app.voice.turn_metrics import TurnTiming, voice_latency_stats

logger = get_logger(__name__)

SendJson = Callable[[dict], Awaitable[None]]
SendBytes = Callable[[bytes], Awaitable[None]]


class VoiceSession:
    """Runs the reply side of a conversation for one connection."""

    def __init__(
        self,
        *,
        llm_engine: StreamingLLMEngine,
        tts_engine: StreamingTTSEngine,
        send_json: SendJson,
        send_bytes: SendBytes,
        history_turns: Optional[int] = None,
        tts_max_lead_seconds: Optional[float] = None,
    ) -> None:
        self.state = ConversationState()
        self.conversation_id = str(self.state.conversation_id)
        self._send_json = send_json
        self._history_turns = settings.VOICE_HISTORY_TURNS if history_turns is None else history_turns
        self.history: list[dict] = []
        self._timing: Optional[TurnTiming] = None
        self.llm = LLMConsumer(engine=llm_engine, send_json=send_json, conversation_id=self.conversation_id)
        self.tts = TTSConsumer(
            engine=tts_engine,
            send_bytes=send_bytes,
            send_json=send_json,
            conversation_id=self.conversation_id,
            max_lead_seconds=(
                settings.VOICE_TTS_MAX_LEAD_MS / 1000.0 if tts_max_lead_seconds is None else tts_max_lead_seconds
            ),
            on_first_audio=self._on_first_audio,
            on_playback_end=self._on_playback_end,
        )
        self.turn_manager = TurnManager(
            state=self.state,
            on_user_turn_started=self._on_user_turn_started,
            on_user_turn_completed=self._on_user_turn_completed,
            on_user_interrupted=self._on_user_interrupted,
        )

    # ------------------------------------------------------------------ input

    async def process_transcript_event(self, event: TranscriptEvent) -> None:
        """Feed one STT event (partial or final) into turn-taking."""
        await self.turn_manager.process_transcript_event(event)

    async def inject_transcript(self, text: str) -> None:
        """Development helper: behave as if the user had said `text`."""
        utterance_id = str(uuid.uuid4())
        for kind in (TranscriptType.PARTIAL, TranscriptType.FINAL):
            await self.turn_manager.process_transcript_event(
                TranscriptEvent(type=kind, utterance_id=utterance_id, transcript=text, confidence=1.0)
            )

    async def speak_text(self, text: str) -> None:
        """Development helper: speak `text` without calling the LLM."""
        utterance_id = str(uuid.uuid4())
        self._timing = None
        self.state.start_system_turn()
        await self.tts.start_speaking(text=text, utterance_id=utterance_id)

    async def close(self) -> None:
        """Stop everything (the connection is going away)."""
        await self.llm.aclose()
        await self.tts.stop(reason="closed")

    # ------------------------------------------------------------- turn events

    async def _on_user_turn_started(self, _event: UserTurnStarted) -> None:
        # New speech always wins over a reply that is still being generated.
        self.llm.cancel()

    async def _on_user_interrupted(self, _event: UserInterrupted) -> None:
        """Barge-in: stop generating and stop speaking, now."""
        started = time.monotonic()
        if self._timing is not None:
            self._timing.interrupted = True
        self.llm.cancel()
        stopped = await self.tts.stop(reason="barge_in")
        if stopped:
            stop_ms = (time.monotonic() - started) * 1000.0
            voice_latency_stats.record_barge_in(stop_ms)
            await self._safe_send({"type": "barge_in", "server_stop_ms": round(stop_ms, 2)})
            logger.info(
                "Barge-in: reply stopped",
                extra_fields={"conversation_id": self.conversation_id, "server_stop_ms": round(stop_ms, 2)},
            )

    async def _on_user_turn_completed(self, event: UserTurnCompleted) -> None:
        """The user finished a sentence: generate and speak the reply."""
        text = event.transcript.strip()
        if not text:
            return
        timing = TurnTiming(utterance_id=event.utterance_id)
        self._timing = timing
        history = list(self.history)
        self._remember("user", text)
        # The system turn lasts until the reply has been heard, not just generated.
        self.state.start_system_turn()
        await self.tts.begin(event.utterance_id)

        async def on_segment(segment: str) -> None:
            timing.mark_first_segment()
            await self.tts.speak(segment)

        async def on_complete(full_text: str, outcome: str) -> None:
            if full_text.strip():
                self._remember("assistant", full_text.strip())
            if outcome != CANCELLED:
                await self.tts.finish()

        await self.llm.start_generation(
            text,
            event.utterance_id,
            history=history,
            on_first_token=timing.mark_llm_first_token,
            on_segment=on_segment,
            on_complete=on_complete,
        )

    # ------------------------------------------------------------ speech events

    def _on_first_audio(self, utterance_id: str) -> None:
        if self._timing is not None and self._timing.utterance_id == utterance_id:
            self._timing.mark_first_audio()

    async def _on_playback_end(self, utterance_id: str, interrupted: bool) -> None:
        timing = self._timing
        if timing is not None and timing.utterance_id == utterance_id:
            timing.interrupted = timing.interrupted or interrupted
            voice_latency_stats.record_turn(timing)
            await self._safe_send(timing.to_payload())
            self._timing = None
        if not interrupted and not self.llm.is_generating and self.tts.current_utterance_id in (None, utterance_id):
            self.state.complete_system_turn()

    # ---------------------------------------------------------------- helpers

    def _remember(self, role: str, content: str) -> None:
        if self._history_turns <= 0:
            return
        self.history.append({"role": role, "content": content})
        overflow = len(self.history) - self._history_turns * 2
        if overflow > 0:
            del self.history[:overflow]

    async def _safe_send(self, payload: dict) -> None:
        try:
            await self._send_json(payload)
        except Exception:  # the socket may already be closed
            pass
