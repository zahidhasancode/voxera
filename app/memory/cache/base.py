"""Memory cache abstraction — Redis-ready port."""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class MemoryCache(ABC):
    @abstractmethod
    async def get(self, namespace: str, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def set(self, namespace: str, key: str, value: Any, *, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, namespace: str, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_namespace(self, namespace: str) -> None:
        raise NotImplementedError

    @staticmethod
    def build_key(*parts: Any) -> str:
        payload = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()


class _CacheEntry:
    def __init__(self, value: Any, expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at

    @property
    def expired(self) -> bool:
        return time.monotonic() > self.expires_at


class InMemoryMemoryCache(MemoryCache):
    """Process-local cache — swap for RedisMemoryCache in production cluster."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, _CacheEntry]] = {}
        self.hits = 0
        self.misses = 0

    async def get(self, namespace: str, key: str) -> Any | None:
        bucket = self._store.get(namespace, {})
        entry = bucket.get(key)
        if entry is None or entry.expired:
            self.misses += 1
            if entry and entry.expired:
                del bucket[key]
            return None
        self.hits += 1
        return entry.value

    async def set(self, namespace: str, key: str, value: Any, *, ttl_seconds: int) -> None:
        bucket = self._store.setdefault(namespace, {})
        bucket[key] = _CacheEntry(value, time.monotonic() + ttl_seconds)

    async def delete(self, namespace: str, key: str) -> None:
        bucket = self._store.get(namespace)
        if bucket and key in bucket:
            del bucket[key]

    async def clear_namespace(self, namespace: str) -> None:
        self._store.pop(namespace, None)
