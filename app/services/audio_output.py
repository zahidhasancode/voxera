"""Audio output control for managing downstream audio playback."""

import asyncio
from typing import Dict, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class AudioOutputController:
    """Controls audio output and handles stop signals for barge-in."""

    def __init__(self):
        """Initialize audio output controller."""
        self._stop_events: Dict[str, asyncio.Event] = {}
        self._active_outputs: Dict[str, bool] = {}

    def create_stop_event(self, call_id: str) -> asyncio.Event:
        """Create a stop event for a call session.

        Args:
            call_id: Call session ID

        Returns:
            asyncio.Event that can be used to signal stop
        """
        if call_id not in self._stop_events:
            self._stop_events[call_id] = asyncio.Event()
        return self._stop_events[call_id]

    def stop_output(self, call_id: str) -> None:
        """Signal to stop audio output for a call session.

        Args:
            call_id: Call session ID
        """
        if call_id in self._stop_events:
            self._stop_events[call_id].set()
            self._active_outputs[call_id] = False
            logger.info(
                "Audio output stop signaled",
                extra_fields={"call_id": call_id},
            )

    def reset_stop_event(self, call_id: str) -> None:
        """Reset stop event for a call session (when starting new output).

        Args:
            call_id: Call session ID
        """
        if call_id in self._stop_events:
            self._stop_events[call_id].clear()
            self._active_outputs[call_id] = True

    def is_stopped(self, call_id: str) -> bool:
        """Check if audio output should be stopped.

        Args:
            call_id: Call session ID

        Returns:
            True if stop signal is set, False otherwise
        """
        if call_id not in self._stop_events:
            return False
        return self._stop_events[call_id].is_set()

    async def wait_for_stop(self, call_id: str, timeout: Optional[float] = None) -> bool:
        """Wait for stop signal.

        Args:
            call_id: Call session ID
            timeout: Optional timeout in seconds

        Returns:
            True if stop signal received, False if timeout
        """
        if call_id not in self._stop_events:
            return False

        try:
            await asyncio.wait_for(
                self._stop_events[call_id].wait(), timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False

    def cleanup(self, call_id: str) -> None:
        """Clean up stop event for a call session.

        Args:
            call_id: Call session ID
        """
        self._stop_events.pop(call_id, None)
        self._active_outputs.pop(call_id, None)

    def is_output_active(self, call_id: str) -> bool:
        """Check if output is currently active for a call.

        Args:
            call_id: Call session ID

        Returns:
            True if output is active, False otherwise
        """
        return self._active_outputs.get(call_id, False)


# Global audio output controller
audio_output_controller = AudioOutputController()
