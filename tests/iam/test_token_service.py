"""Token service tests."""

from uuid import uuid4

import pytest

from app.iam.auth.token_service import TokenService


def test_create_and_decode_access_token():
    service = TokenService()
    user_id = uuid4()
    token = service.create_access_token(user_id=user_id, role_slug="administrator")
    payload = service.decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["role"] == "administrator"


def test_invalid_token_raises():
    service = TokenService()
    with pytest.raises(Exception):
        service.decode_token("not.a.valid.token")
