"""Credential encryption tests."""

import pytest

from app.integrations.credentials.store import credential_store


@pytest.mark.unit
def test_encrypt_decrypt_roundtrip():
    payload = {"access_token": "secret-token", "refresh_token": "refresh"}
    encrypted = credential_store.encrypt_payload(payload)
    assert "secret-token" not in encrypted
    decrypted = credential_store.decrypt_payload(encrypted)
    assert decrypted["access_token"] == "secret-token"


@pytest.mark.unit
def test_redact_for_response():
    redacted = credential_store.redact_for_response(
        {"access_token": "x", "api_key": "y", "scope": "read"}
    )
    assert redacted["access_token"] == "***"
    assert redacted["api_key"] == "***"
    assert redacted["scope"] == "read"
