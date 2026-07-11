"""API key generation and verification — secrets never stored in plaintext."""

import hashlib
import hmac
import secrets

from app.core.config import settings


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, prefix, hash). Full key shown once only."""
    raw = secrets.token_urlsafe(32)
    full_key = f"{settings.IAM_API_KEY_PREFIX}{raw}"
    prefix = full_key[:12]
    key_hash = _hash_key(full_key)
    return full_key, prefix, key_hash


def _hash_key(key: str) -> str:
    return hmac.new(settings.api_key_secret.encode(), key.encode(), hashlib.sha256).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    return hmac.compare_digest(_hash_key(key), key_hash)
