"""SSO provider abstraction — SAML 2.0 and OIDC."""

from abc import ABC, abstractmethod


class SsoProviderBase(ABC):
    @property
    @abstractmethod
    def provider_type(self) -> str: ...

    @abstractmethod
    async def initiate_login(self, *, relay_state: str) -> str: ...

    @abstractmethod
    async def handle_callback(self, *, payload: dict) -> dict: ...

    @abstractmethod
    async def validate_metadata(self, config: dict) -> list[str]: ...
