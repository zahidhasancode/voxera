"""Knowledge domain helpers."""

from uuid import UUID

from app.knowledge.retrieval.vector_store import VectorStore


def build_vector_namespace(tenant_id: UUID, source_id: UUID) -> str:
    return VectorStore.build_tenant_namespace(tenant_id, source_id)
