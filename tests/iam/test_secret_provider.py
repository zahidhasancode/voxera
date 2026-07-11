"""Secret provider tests."""

from app.iam.security.secret_provider import LocalSecretProvider


def test_encrypt_decrypt_roundtrip():
    provider = LocalSecretProvider()
    encrypted = provider.encrypt("super-secret-api-token")
    assert encrypted != "super-secret-api-token"
    assert provider.decrypt(encrypted) == "super-secret-api-token"
