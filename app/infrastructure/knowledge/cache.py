"""In-process TTL cache for knowledge embeddings and retrieval."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any


class KnowledgeCache:
    """Thread-safe TTL cache for embeddings and retrieval results."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if expires_at < time.monotonic():
                del self._store[key]
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self._ttl, value)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {"hits": self.hits, "misses": self.misses, "size": len(self._store)}


def _build_cache() -> KnowledgeCache:
    from app.core.config import settings

    return KnowledgeCache(ttl_seconds=settings.KNOWLEDGE_CACHE_TTL_SECONDS)


knowledge_cache = _build_cache()
