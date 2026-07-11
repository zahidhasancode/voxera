"""Webhook signature and idempotency tests."""

import pytest

from app.integrations.webhooks.signature import webhook_signature_validator


@pytest.mark.unit
def test_hmac_sha256_validation():
    payload = b'{"event":"test"}'
    secret = "webhook-secret"
    import hashlib
    import hmac

    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert webhook_signature_validator.validate_hmac_sha256(
        payload=payload,
        signature=sig,
        secret=secret,
    )


@pytest.mark.unit
def test_payload_hash_deterministic():
    payload = {"id": "1", "type": "order.created"}
    h1 = webhook_signature_validator.payload_hash(payload)
    h2 = webhook_signature_validator.payload_hash(payload)
    assert h1 == h2


@pytest.mark.unit
def test_timestamp_validation_accepts_recent():
    import time

    assert webhook_signature_validator.validate_timestamp(str(int(time.time())))
