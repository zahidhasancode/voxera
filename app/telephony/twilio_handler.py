"""Twilio inbound voice handler: TwiML webhook and Media Streams WebSocket.

Exposes:
- POST /twilio/inbound: Returns TwiML that connects the call to the stream WebSocket.
- WebSocket /twilio/stream: Twilio Media Streams endpoint (start/media/stop, base64 decode, per-call session).

Integrates Twilio audio with STT pipeline: decoded PCM frames are fed into STT;
transcripts are injected into TurnManager. Barge-in supported; event loop not blocked.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.core.config import settings
from app.core.logger import get_logger
from app.telephony.twilio_validation import require_twilio_signature
from app.telephony.twilio_stream import (
    TwilioStreamSession,
    handle_twilio_event,
    parse_twilio_message,
)
from app.telephony.call_session import CallSession
from app.telephony.session_registry import call_session_registry
from app.telephony.stream_auth import build_signed_stream_url, verify_stream_token
from app.telephony.telephony_log import log_telephony

logger = get_logger(__name__)

router = APIRouter(prefix="/twilio", tags=["telephony-twilio"])


def _build_stream_url(request: Request) -> str:
    """Build the public wss:// URL for the Twilio stream endpoint.

    Uses TWILIO_PUBLIC_BASE_URL when set (recommended for production);
    otherwise derives from the request (Host header, correct scheme).
    """
    base = (settings.TWILIO_PUBLIC_BASE_URL or "").strip()
    if base:
        # Normalize: ensure no trailing slash, ensure wss
        base = base.rstrip("/")
        if base.startswith("http://"):
            base = "wss" + base[4:]
        elif base.startswith("https://"):
            base = "wss" + base[5:]
        elif not base.startswith("wss://"):
            base = f"wss://{base}"
        return f"{base}/twilio/stream"
    # Derive from request (works behind proxies that set Host/X-Forwarded-*)
    url = request.url
    netloc = url.netloc or request.headers.get("host", "localhost:8000")
    scheme = "wss" if url.scheme == "https" else "wss"
    return f"{scheme}://{netloc}/twilio/stream"


def _twiml_connect_stream(stream_url: str, call_sid: str | None = None) -> str:
    """Build TwiML Response with Connect/Stream for bidirectional Media Stream."""
    if call_sid:
        stream_url = build_signed_stream_url(stream_url, call_sid)
    root = ET.Element("Response")
    connect = ET.SubElement(root, "Connect")
    ET.SubElement(connect, "Stream", url=stream_url)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root,
        encoding="unicode",
        method="xml",
    )


@router.post(
    "/inbound",
    response_class=Response,
    summary="Twilio voice webhook",
    description="Returns TwiML that connects the incoming call to the Media Stream WebSocket.",
)
async def twilio_inbound(
    request: Request,
    form: dict[str, str] = Depends(require_twilio_signature),
) -> Response:
    """Handle Twilio inbound voice webhook.

    Twilio sends a POST with form fields (CallSid, From, To, etc.).
    We respond with TwiML that connects the call to wss://<host>/twilio/stream.
    """
    stream_url = _build_stream_url(request)
    logger.info(
        "Twilio inbound webhook",
        extra_fields={
            "stream_url": stream_url,
            "call_sid": form.get("CallSid"),
        },
    )
    twiml = _twiml_connect_stream(stream_url, form.get("CallSid"))
    return Response(
        content=twiml,
        media_type="application/xml",
        status_code=200,
    )


@router.websocket("/stream")
async def twilio_stream_websocket(websocket: WebSocket) -> None:
    """Twilio Media Streams WebSocket endpoint."""
    expected_call_sid = websocket.query_params.get("call_sid")
    token = websocket.query_params.get("token")
    auth_token = (settings.TWILIO_AUTH_TOKEN or "").strip()
    if auth_token:
        if not expected_call_sid or not token:
            await websocket.close(code=4403)
            return
        try:
            verify_stream_token(expected_call_sid, token)
        except Exception:
            await websocket.close(code=4403)
            return

    await websocket.accept()
    logger.info("Twilio Media Stream WebSocket connected")
    session: Optional[TwilioStreamSession] = None
    call_session: Optional[CallSession] = None
    try:
        while True:
            data = await websocket.receive_text()
            raw = (data or "").strip()
            if not raw:
                continue
            payload = parse_twilio_message(raw)
            if payload is None:
                continue
            try:
                # Detect "stop" event immediately and tear down first
                if (payload or {}).get("event") == "stop":
                    if call_session is not None:
                        await call_session.stop()
                        call_session = None
                    session, decoded_chunk = handle_twilio_event(payload, session)
                    continue
                session, decoded_chunk = handle_twilio_event(payload, session)

                # Create call session on first session (stream start)
                if session is not None and call_session is None:
                    if expected_call_sid and session.call_sid != expected_call_sid:
                        log_telephony(
                            "error",
                            call_sid=session.call_sid,
                            stream_sid=session.stream_sid,
                            level="warning",
                            component="stream_auth",
                            reason="call_sid_mismatch",
                        )
                        await websocket.close(code=4403)
                        return
                    call_session = CallSession(
                        call_sid=session.call_sid,
                        stream_sid=session.stream_sid,
                    )
                    async def silence_hangup() -> None:
                        await websocket.close()
                    await call_session.start(
                        send_text=websocket.send_text,
                        send_json=websocket.send_json,
                        on_silence_hangup=silence_hangup,
                    )
                    await call_session_registry.register(
                        call_sid=session.call_sid,
                        stream_sid=session.stream_sid,
                        conversation_id=str(call_session.conversation_id),
                    )

                # Feed decoded μ-law into STT (convert to PCM, buffer, dispatch frames)
                if decoded_chunk and call_session:
                    await call_session_registry.heartbeat(call_session.call_sid)
                    await call_session_registry.update_state(
                        call_session.call_sid,
                        call_session.state.value,
                    )
                    await call_session.feed_mulaw(decoded_chunk)

                # Teardown when stream stops (session cleared)
                if session is None and call_session is not None:
                    await call_session_registry.unregister(call_session.call_sid)
                    await call_session.stop()
                    call_session = None

                # Optional: legacy on_audio_chunk if session has one set
                if decoded_chunk and session and session.on_audio_chunk:
                    try:
                        await session.on_audio_chunk(
                            session.stream_sid,
                            session.call_sid,
                            decoded_chunk,
                        )
                    except Exception as e:
                        log_telephony(
                            "error",
                            call_sid=session.call_sid,
                            stream_sid=session.stream_sid,
                            level="warning",
                            component="on_audio_chunk",
                            error=str(e),
                        )
            except Exception as e:
                log_telephony(
                    "error",
                    call_sid=session.call_sid if session else None,
                    stream_sid=session.stream_sid if session else None,
                    conversation_id=str(call_session.conversation_id) if call_session else None,
                    state=call_session.state.value if call_session else None,
                    level="error",
                    component="message_handling",
                    error=str(e),
                    exc_info=True,
                )
                # Do not re-raise: keep WebSocket alive unless disconnect or fatal
    except WebSocketDisconnect:
        log_telephony(
            "disconnect",
            call_sid=getattr(session, "call_sid", None) if session else None,
            stream_sid=getattr(session, "stream_sid", None) if session else None,
            conversation_id=str(call_session.conversation_id) if call_session else None,
            state=call_session.state.value if call_session else None,
            level="debug",
            reason="peer_closed_or_network",
            had_call_session=call_session is not None,
        )
        if call_session:
            try:
                await call_session_registry.unregister(call_session.call_sid)
                await call_session.stop()
            except Exception as e:
                log_telephony(
                    "error",
                    call_sid=call_session.call_sid,
                    stream_sid=call_session.stream_sid,
                    conversation_id=str(call_session.conversation_id),
                    state=call_session.state.value,
                    level="warning",
                    component="stop_on_disconnect",
                    error=str(e),
                )
            call_session = None
    except Exception as e:
        if call_session:
            try:
                await call_session_registry.unregister(call_session.call_sid)
                await call_session.stop()
            except Exception as stop_err:
                log_telephony(
                    "error",
                    call_sid=call_session.call_sid,
                    stream_sid=call_session.stream_sid,
                    conversation_id=str(call_session.conversation_id),
                    state=call_session.state.value,
                    level="warning",
                    component="stop_on_error",
                    error=str(stop_err),
                )
            call_session = None
        log_telephony(
            "error",
            call_sid=session.call_sid if session else None,
            stream_sid=session.stream_sid if session else None,
            level="error",
            component="websocket",
            error=str(e),
            exc_info=True,
        )
