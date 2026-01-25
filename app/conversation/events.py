"""Internal conversation events."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class UserTurnStarted:
    """Event emitted when a user turn starts."""

    utterance_id: str
    timestamp: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class UserTurnCompleted:
    """Event emitted when a user turn completes."""

    utterance_id: str
    transcript: str
    timestamp: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class UserInterrupted:
    """Event emitted when user interrupts system (barge-in)."""

    timestamp: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
