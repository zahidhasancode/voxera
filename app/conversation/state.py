"""Conversation state tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ConversationState:
    """Tracks the state of an active conversation."""

    conversation_id: UUID = field(default_factory=uuid4)
    current_utterance_id: UUID | None = None
    last_user_activity: datetime = field(default_factory=datetime.utcnow)
    is_user_speaking: bool = False
    is_system_speaking: bool = False
    turn_count: int = 0

    def start_user_turn(self, utterance_id: str | UUID) -> None:
        """Mark the start of a user turn.

        Args:
            utterance_id: Unique identifier for this utterance (str or UUID)
        """
        # Convert string to UUID if needed
        if isinstance(utterance_id, str):
            self.current_utterance_id = UUID(utterance_id)
        else:
            self.current_utterance_id = utterance_id
        self.is_user_speaking = True
        self.last_user_activity = datetime.utcnow()

    def complete_user_turn(self) -> None:
        """Mark the completion of a user turn."""
        self.is_user_speaking = False
        self.current_utterance_id = None
        self.turn_count += 1
        self.last_user_activity = datetime.utcnow()

    def start_system_turn(self) -> None:
        """Mark the start of a system turn."""
        self.is_system_speaking = True

    def complete_system_turn(self) -> None:
        """Mark the completion of a system turn."""
        self.is_system_speaking = False

    def interrupt_user(self) -> None:
        """Handle user interruption (barge-in)."""
        if self.is_user_speaking:
            self.is_user_speaking = False
            self.current_utterance_id = None

    def to_dict(self) -> dict:
        """Convert state to dictionary for logging/debugging."""
        return {
            "conversation_id": str(self.conversation_id),
            "current_utterance_id": str(self.current_utterance_id) if self.current_utterance_id else None,
            "last_user_activity": self.last_user_activity.isoformat(),
            "is_user_speaking": self.is_user_speaking,
            "is_system_speaking": self.is_system_speaking,
            "turn_count": self.turn_count,
        }
