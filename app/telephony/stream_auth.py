"""Twilio Media Stream authentication and replay protection."""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode

from fastapi import HTTPException, WebSocket, status

from app.core.config import settings


def sign_stream_token(call_sid: str, *, issued_at: int | None = None) -> str:
    """Create HMAC token binding call_sid and timestamp."""
    secret = (settings.TWILIO_AUTH_TOKEN or settings.SECRET_KEY or "").encode("utf-8")
    if not secret:
        raise ValueError("TWILIO_AUTH_TOKEN required for stream signing")
    ts = issued_at if issued_at is not None else int(time.time())
    payload = f"{call_sid}:{ts}".encode("utf-8")
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"{ts}.{digest}"


def build_signed_stream_url(base_stream_url: str, call_sid: str) -> str:
    token = sign_stream_token(call_sid)
    query = urlencode({"token": token, "call_sid": call_sid})
    separator = "&" if "?" in base_stream_url else "?"
    return f"{base_stream_url}{separator}{query}"


def verify_stream_token(call_sid: str, token: str) -> None:
    if not token or "." not in token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid stream token")
    ts_str, digest = token.split(".", 1)
    try:
        issued_at = int(ts_str)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid stream token") from exc
    if time.time() - issued_at > settings.TWILIO_STREAM_TOKEN_TTL_SECONDS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Stream token expired")
    expected = sign_stream_token(call_sid, issued_at=issued_at).split(".", 1)[1]
    if not hmac.compare_digest(expected, digest):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid stream token")


async def require_twilio_stream_auth(websocket: WebSocket) -> str:
    """Validate signed stream token from query params before accepting WS."""
    call_sid = websocket.query_params.get("call_sid")
    token = websocket.query_params.get("token")
    auth_token = (settings.TWILIO_AUTH_TOKEN or "").strip()
    if not auth_token:
        if settings.is_production or settings.is_staging:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio stream authentication is not configured",
            )
        return call_sid or "development"
    if not call_sid or not token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing stream authentication")
    verify_stream_token(call_sid, token)
    return call_sid
