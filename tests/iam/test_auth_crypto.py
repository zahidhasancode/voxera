"""Password and API key crypto tests."""

from app.iam.api_keys.key_crypto import generate_api_key, verify_api_key
from app.iam.auth.password import hash_password, verify_password


def test_password_hash_and_verify():
    hashed = hash_password("SecurePassword123!")
    assert hashed != "SecurePassword123!"
    assert verify_password("SecurePassword123!", hashed)
    assert not verify_password("wrong", hashed)


def test_api_key_generate_and_verify():
    full_key, prefix, key_hash = generate_api_key()
    assert full_key.startswith("vx_")
    assert len(prefix) == 12
    assert verify_api_key(full_key, key_hash)
    assert not verify_api_key("vx_invalid", key_hash)
