"""Encrypted credential storage for integrations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.enums import IntegrationCredentialType
from app.iam.security.secret_provider import get_secret_provider


class CredentialStore:
    """Encrypt/decrypt integration secrets — never expose plaintext outside service layer."""

    def __init__(self) -> None:
        self._provider = get_secret_provider()

    def encrypt_payload(self, payload: dict[str, Any]) -> str:
        return self._provider.encrypt(json.dumps(payload))

    def decrypt_payload(self, encrypted: str) -> dict[str, Any]:
        return json.loads(self._provider.decrypt(encrypted))

    def redact_for_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if key in {"access_token", "refresh_token", "api_key", "client_secret", "password"}:
                redacted[key] = "***"
            else:
                redacted[key] = value
        return redacted

    @staticmethod
    def credential_expired(expires_at: datetime | None) -> bool:
        if expires_at is None:
            return False
        return expires_at <= datetime.now(timezone.utc)


credential_store = CredentialStore()
