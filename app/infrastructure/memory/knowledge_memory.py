"""Session-scoped knowledge memory using MemoryCache."""

from uuid import UUID

from app.core.config import settings
from app.memory.cache.base import MemoryCache
from app.memory.interfaces.memory_types import KnowledgeMemory


class CachedKnowledgeMemory(KnowledgeMemory):
    """Stores retrieved knowledge excerpts per session without calling RAG."""

    _KEY = "knowledge_excerpts"

    def __init__(self, cache: MemoryCache) -> None:
        self._cache = cache

    def _namespace(self, tenant_id: UUID, conversation_id: UUID) -> str:
        return f"memory-{tenant_id}-{conversation_id}"

    async def attach(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
        excerpts: list[str],
    ) -> None:
        existing = await self.get(tenant_id, agent_id, conversation_id)
        merged = list(dict.fromkeys(existing + excerpts))
        await self._cache.set(
            self._namespace(tenant_id, conversation_id),
            self._KEY,
            merged,
            ttl_seconds=settings.MEMORY_CACHE_TTL_SECONDS,
        )

    async def get(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        conversation_id: UUID,
    ) -> list[str]:
        cached = await self._cache.get(
            self._namespace(tenant_id, conversation_id),
            self._KEY,
        )
        return cached or []
