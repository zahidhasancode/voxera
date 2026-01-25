"""Turn-taking manager for conversation flow."""

from typing import Callable, Optional, Union

from app.core.logger import get_logger
from app.conversation.events import UserInterrupted, UserTurnCompleted, UserTurnStarted
from app.conversation.state import ConversationState
from app.stt.models import TranscriptEvent, TranscriptType

logger = get_logger(__name__)


class TurnManager:
    """Manages conversation turn-taking and state.

    Tracks user turns, detects turn completion, and emits events
    for downstream processing (LLM, TTS, etc.).
    """

    def __init__(
        self,
        state: ConversationState,
        on_user_turn_started: Optional[Callable[[UserTurnStarted], None]] = None,
        on_user_turn_completed: Optional[Callable[[UserTurnCompleted], None]] = None,
        on_user_interrupted: Optional[Callable[[UserInterrupted], None]] = None,
    ):
        """Initialize turn manager.

        Args:
            state: ConversationState instance to manage
            on_user_turn_started: Optional callback for user turn started events
            on_user_turn_completed: Optional callback for user turn completed events
            on_user_interrupted: Optional callback for user interruption events
        """
        self.state = state
        self.on_user_turn_started = on_user_turn_started
        self.on_user_turn_completed = on_user_turn_completed
        self.on_user_interrupted = on_user_interrupted

    async def process_transcript_event(self, event: TranscriptEvent) -> None:
        """Process a transcript event and update conversation state.

        Args:
            event: TranscriptEvent from STT (partial or final)
        """
        if event.type == TranscriptType.PARTIAL:
            # Barge-in: user started speaking while system was responding
            if self.state.is_system_speaking:
                await self.handle_interruption()

            # Partial transcript - user is still speaking
            if not self.state.is_user_speaking:
                # New user turn started
                self.state.start_user_turn(event.utterance_id)
                logger.info(
                    "User turn started",
                    extra_fields={
                        "conversation_id": str(self.state.conversation_id),
                        "utterance_id": event.utterance_id,
                        "turn_count": self.state.turn_count,
                    },
                )

                # Emit UserTurnStarted event
                turn_started = UserTurnStarted(
                    utterance_id=event.utterance_id,
                )
                if self.on_user_turn_started:
                    await self._call_callback(self.on_user_turn_started, turn_started)

            # Update last activity timestamp
            self.state.last_user_activity = event.timestamp

        elif event.type == TranscriptType.FINAL:
            # Final transcript - user turn is complete
            if self.state.is_user_speaking:
                logger.info(
                    "User turn completed",
                    extra_fields={
                        "conversation_id": str(self.state.conversation_id),
                        "utterance_id": event.utterance_id,
                        "transcript": event.transcript,
                        "turn_count": self.state.turn_count,
                        "confidence": round(event.confidence, 3),
                    },
                )

                # Mark turn as complete
                self.state.complete_user_turn()

                # Emit UserTurnCompleted event
                turn_completed = UserTurnCompleted(
                    utterance_id=event.utterance_id,
                    transcript=event.transcript,
                )
                if self.on_user_turn_completed:
                    await self._call_callback(self.on_user_turn_completed, turn_completed)

                logger.debug(
                    "USER_TURN_COMPLETE event emitted",
                    extra_fields={
                        "conversation_id": str(self.state.conversation_id),
                        "utterance_id": event.utterance_id,
                        "transcript_length": len(event.transcript),
                    },
                )
            else:
                # Final transcript but we weren't tracking a user turn
                # This might happen if we missed the partial transcripts
                logger.debug(
                    "Final transcript received but no active user turn",
                    extra_fields={
                        "conversation_id": str(self.state.conversation_id),
                        "utterance_id": event.utterance_id,
                        "transcript": event.transcript,
                    },
                )

    async def handle_interruption(self) -> None:
        """Handle user interruption (barge-in).

        Called when user starts speaking during system response.
        """
        if self.state.is_system_speaking:
            logger.info(
                "User interrupted system",
                extra_fields={
                    "conversation_id": str(self.state.conversation_id),
                    "turn_count": self.state.turn_count,
                },
            )
            self.state.interrupt_user()
            self.state.complete_system_turn()

            # Emit UserInterrupted event
            interrupted = UserInterrupted()
            if self.on_user_interrupted:
                await self._call_callback(self.on_user_interrupted, interrupted)

    async def _call_callback(
        self, callback: Callable, event: Union[UserTurnStarted, UserTurnCompleted, UserInterrupted]
    ) -> None:
        """Call callback function (async or sync).

        Args:
            callback: Callback function to call
            event: Event to pass to callback
        """
        import asyncio

        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(
                "Error in turn manager callback",
                extra_fields={
                    "callback_name": callback.__name__ if hasattr(callback, "__name__") else "unknown",
                    "event_type": type(event).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
