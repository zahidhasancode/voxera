"""Webhook signature validation and replay protection."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any


class WebhookSignatureValidator:
    """Validate inbound webhook signatures per provider."""

    MAX_AGE_SECONDS = 300

    def validate_hmac_sha256(
        self,
        *,
        payload: bytes,
        signature: str,
        secret: str,
        prefix: str = "",
    ) -> bool:
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        provided = signature.removeprefix(prefix).strip()
        return hmac.compare_digest(expected, provided)

    def validate_timestamp(self, timestamp_header: str | None) -> bool:
        if not timestamp_header:
            return True
        try:
            ts = int(timestamp_header)
        except ValueError:
            return False
        return abs(time.time() - ts) <= self.MAX_AGE_SECONDS

    def payload_hash(self, payload: dict[str, Any]) -> str:
        canonical = repr(sorted(payload.items())).encode()
        return hashlib.sha256(canonical).hexdigest()


webhook_signature_validator = WebhookSignatureValidator()
