"""MFA factor management abstraction."""

from abc import ABC, abstractmethod


class MfaProviderBase(ABC):
    @property
    @abstractmethod
    def factor_type(self) -> str: ...

    @abstractmethod
    async def enroll(self, *, user_id: str) -> dict: ...

    @abstractmethod
    async def verify(self, *, user_id: str, code: str) -> bool: ...
