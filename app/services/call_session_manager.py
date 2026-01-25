"""CallSession manager for managing call session lifecycle."""

from typing import Dict, Optional

from app.core.logger import get_logger
from app.models.call_session import CallSession, CallState

logger = get_logger(__name__)


class CallSessionManager:
    """Manager for call session instances."""

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, CallSession] = {}

    def create_session(self, call_id: Optional[str] = None) -> CallSession:
        """Create a new call session.

        Args:
            call_id: Optional call ID (generated if not provided)

        Returns:
            New CallSession instance
        """
        session = CallSession(call_id=call_id) if call_id else CallSession()

        self._sessions[session.call_id] = session
        logger.info(
            "Call session created",
            extra_fields={
                "call_id": session.call_id,
                "state": session.state.value,
            },
        )
        return session

    def get_session(self, call_id: str) -> Optional[CallSession]:
        """Get session by call_id.

        Args:
            call_id: Call session ID

        Returns:
            CallSession if found, None otherwise
        """
        return self._sessions.get(call_id)

    def update_session(self, session: CallSession) -> None:
        """Update session in manager.

        Args:
            session: CallSession to update
        """
        if session.call_id in self._sessions:
            self._sessions[session.call_id] = session
            logger.debug(
                "Call session updated",
                extra_fields={
                    "call_id": session.call_id,
                    "state": session.state.value,
                },
            )

    def end_session(self, call_id: str) -> Optional[CallSession]:
        """End a call session.

        Args:
            call_id: Call session ID

        Returns:
            Ended CallSession if found, None otherwise
        """
        session = self.get_session(call_id)
        if session:
            session.transition_to(CallState.ENDED)
            duration = session.get_total_duration()
            
            # Log final ASR latency statistics
            asr_stats = session.get_asr_latency_stats()
            
            extra_fields = {
                "call_id": session.call_id,
                "duration": duration,
            }
            
            if asr_stats.get("count", 0) > 0:
                extra_fields.update({
                    "asr_latency_count": asr_stats["count"],
                    "asr_latency_p50_ms": round(asr_stats["p50"], 2),
                    "asr_latency_p95_ms": round(asr_stats["p95"], 2),
                    "asr_latency_avg_ms": round(asr_stats["avg"], 2),
                    "asr_latency_min_ms": round(asr_stats["min"], 2),
                    "asr_latency_max_ms": round(asr_stats["max"], 2),
                })
            
            logger.info(
                "Call session ended",
                extra_fields=extra_fields,
            )
        return session

    def remove_session(self, call_id: str) -> bool:
        """Remove session from manager.

        Args:
            call_id: Call session ID

        Returns:
            True if session was removed, False otherwise
        """
        if call_id in self._sessions:
            del self._sessions[call_id]
            logger.debug("Call session removed", extra_fields={"call_id": call_id})
            return True
        return False

    def list_active_sessions(self) -> list[CallSession]:
        """Get list of active (non-ended) sessions.

        Returns:
            List of active CallSession instances
        """
        return [s for s in self._sessions.values() if s.is_active()]

    def get_session_count(self) -> int:
        """Get total number of sessions.

        Returns:
            Number of sessions
        """
        return len(self._sessions)

    def cleanup_ended_sessions(self) -> int:
        """Remove all ended sessions from manager.

        Returns:
            Number of sessions removed
        """
        ended = [call_id for call_id, session in self._sessions.items() if session.is_ended()]
        for call_id in ended:
            self.remove_session(call_id)
        return len(ended)


# Global session manager instance
session_manager = CallSessionManager()
