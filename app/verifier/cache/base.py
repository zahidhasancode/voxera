"""Verifier cache abstraction."""

import time
from abc import ABC, abstractmethod
from typing import Any


class VerifierCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        ...


class InMemoryVerifierCache(VerifierCache):
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires = entry
        if time.time() > expires:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        self._store[key] = (value, time.time() + ttl_seconds)
