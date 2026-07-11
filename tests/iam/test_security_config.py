"""Security configuration validation."""

import pytest

from app.core.config import Settings, _INSECURE_DEFAULT_SECRET


def test_separate_secrets_resolve_in_development():
    settings = Settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY="jwt-secret-key-at-least-32-characters-long",
        API_KEY_SECRET="api-key-secret-at-least-32-characters-long",
        ENCRYPTION_SECRET_KEY="encryption-secret-32-characters!!",
    )
    assert len(settings.jwt_secret_key) >= 32
    assert len(settings.api_key_secret) >= 32
    assert len(settings.encryption_secret_key) >= 32


def test_production_rejects_insecure_jwt_secret():
    settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY=_INSECURE_DEFAULT_SECRET,
        API_KEY_SECRET="api-key-secret-at-least-32-characters-long",
        ENCRYPTION_SECRET_KEY="encryption-secret-32-characters!!",
        DATABASE_URL="postgresql+asyncpg://u:p@localhost/db",
    )
    with pytest.raises(RuntimeError):
        settings.validate_security_settings()


def test_missing_jwt_secret_raises(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    settings = Settings(
        ENVIRONMENT="development",
        JWT_SECRET_KEY=None,
        API_KEY_SECRET=None,
        ENCRYPTION_SECRET_KEY=None,
        SECRET_KEY=None,
    )
    with pytest.raises(RuntimeError):
        _ = settings.jwt_secret_key
