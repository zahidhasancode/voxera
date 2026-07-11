"""JWT and token security tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core.config import settings
from app.iam.auth.token_service import TokenService


@pytest.mark.security
def test_tampered_jwt_payload_rejected():
    service = TokenService()
    token = service.create_access_token(user_id=uuid4(), role_slug="administrator")
    parts = token.split(".")
    assert len(parts) == 3
    tampered = f"{parts[0]}.{parts[1]}.invalidsignature"
    with pytest.raises(Exception):
        service.decode_token(tampered)


@pytest.mark.security
def test_expired_jwt_rejected():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid4()),
        "type": "access",
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    expired = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    service = TokenService()
    with pytest.raises(Exception):
        service.decode_token(expired)


@pytest.mark.security
def test_wrong_signing_key_rejected():
    payload = {"sub": str(uuid4()), "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = jwt.encode(payload, "wrong-key-wrong-key-wrong-key-wrong!", algorithm="HS256")
    service = TokenService()
    with pytest.raises(Exception):
        service.decode_token(token)
