"""Twilio Media Streams: session state and message handling.

Handles "connected", "start", "media", "stop" events; decodes base64 audio
from "media" events (Twilio sends audio/x-mulaw, 8 kHz, mono); maintains
per-call session state. No STT integration—decoded audio is prepared for
further processing (buffer + optional callback).
"""

import base64
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TwilioStreamSession:
    """Per-call session state for a Twilio Media Stream.

    Created on "start", updated by "media" (decoded audio appended),
    cleared on "stop". Decoded audio is mulaw 8kHz mono bytes.
    """

    stream_sid: str
    call_sid: str
    account_sid: str
    tracks: list[str]
    media_format: dict[str, Any]
    # Decoded audio chunks (mulaw 8 kHz mono bytes) in order; ready for downstream (e.g. STT).
    decoded_audio: bytearray = field(default_factory=bytearray)
    # Optional: call this for each decoded chunk for real-time pipeline (e.g. future STT).
    on_audio_chunk: Optional[Callable[[str, str, bytes], Awaitable[None]]] = None

    @property
    def total_decoded_bytes(self) -> int:
        return len(self.decoded_audio)


def parse_twilio_message(raw: str) -> Optional[dict[str, Any]]:
    """Parse a single Twilio WebSocket JSON message. Returns None on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(
            "Invalid Twilio WebSocket JSON",
            extra_fields={"error": str(e), "raw_preview": raw[:200]},
        )
        return None


def handle_twilio_event(
    payload: dict[str, Any],
    session: Optional[TwilioStreamSession],
) -> tuple[Optional[TwilioStreamSession], Optional[bytes]]:
    """Handle one Twilio event. Returns (updated_session, decoded_chunk_or_none).

    - "connected": returns (None, None); no session yet.
    - "start": returns (new TwilioStreamSession, None).
    - "media": decodes base64 payload, appends to session.decoded_audio; returns (session, decoded_bytes).
    - "stop": returns (None, None); caller should discard session.
    """
    event = (payload.get("event") or "").strip().lower()
    stream_sid = payload.get("streamSid") or ""

    if event == "connected":
        logger.info(
            "Twilio stream connected",
            extra_fields={
                "protocol": payload.get("protocol"),
                "version": payload.get("version"),
            },
        )
        return (session, None)

    if event == "start":
        start = payload.get("start") or {}
        call_sid = start.get("callSid") or ""
        account_sid = start.get("accountSid") or ""
        tracks = start.get("tracks") or []
        media_format = start.get("mediaFormat") or {}
        new_session = TwilioStreamSession(
            stream_sid=stream_sid,
            call_sid=call_sid,
            account_sid=account_sid,
            tracks=tracks,
            media_format=media_format,
        )
        logger.info(
            "Twilio stream started",
            extra_fields={
                "stream_sid": stream_sid,
                "call_sid": call_sid,
                "account_sid": account_sid,
                "tracks": tracks,
            },
        )
        return (new_session, None)

    if event == "media":
        media = payload.get("media") or {}
        b64 = media.get("payload")
        if not b64 or not session:
            return (session, None)
        try:
            decoded = base64.b64decode(b64, validate=True)
        except Exception as e:
            logger.warning(
                "Twilio media payload decode failed",
                extra_fields={
                    "stream_sid": stream_sid,
                    "error": str(e),
                },
            )
            return (session, None)
        session.decoded_audio.extend(decoded)
        return (session, decoded)

    if event == "stop":
        stop = payload.get("stop") or {}
        call_sid = stop.get("callSid") or (session.call_sid if session else "")
        logger.info(
            "Twilio stream stopped",
            extra_fields={
                "stream_sid": stream_sid,
                "call_sid": call_sid,
                "total_decoded_bytes": session.total_decoded_bytes if session else 0,
            },
        )
        return (None, None)

    return (session, None)


def build_twilio_media_message(stream_sid: str, mulaw_payload: bytes) -> str:
    """Build Twilio Media Streams outbound media event JSON.

    Used to send TTS (or other) audio to the call. Payload must be μ-law 8 kHz mono;
    caller is responsible for base64 encoding and JSON shape.

    Returns:
        JSON string: {"event": "media", "streamSid": "<sid>", "media": {"payload": "<base64>"}}
    """
    b64 = base64.b64encode(mulaw_payload).decode("ascii")
    return json.dumps({"event": "media", "streamSid": stream_sid, "media": {"payload": b64}})
