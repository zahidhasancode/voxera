"""Structured JSON logging for telephony pipeline.

Every log includes: event, call_sid, stream_sid, conversation_id (when available),
state (when available), and optional latency metrics. Events are canonical to avoid spam.
"""

from typing import Any, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)

# Canonical events (one log per semantic occurrence)
EVENT_CALL_STARTED = "call_started"
EVENT_FIRST_USER_AUDIO = "first_user_audio"
EVENT_TRANSCRIPT_RECEIVED = "transcript_received"
EVENT_LLM_STARTED = "llm_started"
EVENT_FIRST_TOKEN = "first_token"
EVENT_TTS_STARTED = "tts_started"
EVENT_FIRST_AUDIO_SENT = "first_audio_sent"
EVENT_INTERRUPTION = "interruption"
EVENT_CALL_ENDED = "call_ended"
EVENT_ERROR = "error"


def log_telephony(
    event: str,
    *,
    call_sid: Optional[str] = None,
    stream_sid: Optional[str] = None,
    conversation_id: Optional[str] = None,
    state: Optional[str] = None,
    metrics: Optional[dict[str, Any]] = None,
    level: str = "info",
    message: str = "telephony",
    **extra: Any,
) -> None:
    """Emit one structured telephony log. All fields optional except event. Pass exc_info=True for traceback."""
    payload: dict[str, Any] = {"event": event}
    if call_sid is not None:
        payload["call_sid"] = call_sid
    if stream_sid is not None:
        payload["stream_sid"] = stream_sid
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id
    if state is not None:
        payload["state"] = state
    if metrics is not None:
        payload["metrics"] = metrics
    exc_info = extra.get("exc_info")
    payload.update({k: v for k, v in extra.items() if k != "exc_info"})
    kwargs: dict[str, Any] = {"extra_fields": payload}
    if exc_info is not None:
        kwargs["exc_info"] = exc_info
    getattr(logger, level)(message, **kwargs)
