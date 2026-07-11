"""Twilio stream auth tests."""

import time

import pytest
from fastapi import HTTPException

from app.telephony.stream_auth import build_signed_stream_url, sign_stream_token, verify_stream_token


@pytest.fixture(autouse=True)
def _twilio_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.telephony.stream_auth.settings.TWILIO_AUTH_TOKEN", "test-twilio-auth-token-1234567890")
    monkeypatch.setattr("app.telephony.stream_auth.settings.SECRET_KEY", None)


def test_sign_and_verify_stream_token() -> None:
    token = sign_stream_token("CA123")
    verify_stream_token("CA123", token)


def test_rejects_mismatched_call_sid() -> None:
    token = sign_stream_token("CA123")
    with pytest.raises(HTTPException):
        verify_stream_token("CA999", token)


def test_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.telephony.stream_auth.settings.TWILIO_STREAM_TOKEN_TTL_SECONDS", 60)
    old = int(time.time()) - 120
    token = sign_stream_token("CA123", issued_at=old)
    with pytest.raises(HTTPException, match="expired"):
        verify_stream_token("CA123", token)


def test_build_signed_stream_url() -> None:
    url = build_signed_stream_url("wss://example.com/twilio/stream", "CA123")
    assert "token=" in url
    assert "call_sid=CA123" in url
