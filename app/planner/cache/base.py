"""Planner decision cache abstraction."""

import time
from abc import ABC, abstractmethod
from typing import Any


class PlannerCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...


class InMemoryPlannerCache(PlannerCache):
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        self._store[key] = (value, time.time() + ttl_seconds)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
