"""Secret provider abstraction — local, AWS, Azure, GCP, Vault."""

import base64
import hashlib
from abc import ABC, abstractmethod

from app.core.config import settings


class SecretProvider(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> str: ...

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str: ...


class LocalSecretProvider(SecretProvider):
    """Field-level encryption using SECRET_KEY-derived key (Fernet-like XOR stream)."""

    def _key(self) -> bytes:
        return hashlib.sha256(settings.encryption_secret_key.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        data = plaintext.encode("utf-8")
        key = self._key()
        xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return base64.urlsafe_b64encode(xored).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        data = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
        key = self._key()
        plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return plain.decode("utf-8")


def get_secret_provider() -> SecretProvider:
    provider = settings.IAM_SECRET_PROVIDER.lower()
    if provider == "local":
        return LocalSecretProvider()
    # Future: aws_secrets_manager, azure_key_vault, gcp_secret_manager, vault
    return LocalSecretProvider()
