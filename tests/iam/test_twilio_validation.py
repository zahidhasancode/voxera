"""Twilio signature validation tests."""

import base64
import hashlib
import hmac
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.telephony.twilio_validation import require_twilio_signature


def _sign(url: str, params: list[tuple[str, str]], auth_token: str) -> str:
    data = url + "".join(f"{k}{v}" for k, v in sorted(params))
    digest = hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


@pytest.mark.asyncio
async def test_valid_twilio_signature(monkeypatch):
    auth_token = "twilio-auth-token-for-tests"
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", auth_token)
    monkeypatch.setattr(settings, "TWILIO_PUBLIC_BASE_URL", "https://example.com")

    params = [("CallSid", "CA123"), ("From", "+15551234567")]
    url = "https://example.com/twilio/inbound"
    signature = _sign(url, params, auth_token)

    request = MagicMock()
    request.url.path = "/twilio/inbound"
    request.headers = {"X-Twilio-Signature": signature}
    request.form = AsyncMock(return_value=MagicMock(multi_items=lambda: params))

    result = await require_twilio_signature(request)
    assert result["CallSid"] == "CA123"


@pytest.mark.asyncio
async def test_invalid_twilio_signature(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "twilio-auth-token-for-tests")
    monkeypatch.setattr(settings, "TWILIO_PUBLIC_BASE_URL", "https://example.com")

    request = MagicMock()
    request.url.path = "/twilio/inbound"
    request.headers = {"X-Twilio-Signature": "invalid"}
    request.form = AsyncMock(return_value=MagicMock(multi_items=lambda: [("CallSid", "CA123")]))

    with pytest.raises(HTTPException) as exc:
        await require_twilio_signature(request)
    assert exc.value.status_code == 403
