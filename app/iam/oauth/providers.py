"""OAuth provider abstraction."""

from abc import ABC, abstractmethod


class OAuthProviderBase(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str: ...

    @abstractmethod
    async def get_authorization_url(self, *, redirect_uri: str, state: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, *, code: str, redirect_uri: str) -> dict: ...

    @abstractmethod
    async def get_user_profile(self, *, access_token: str) -> dict: ...
