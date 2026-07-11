"""Knowledge provider registry and startup validation."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.enums import EmbeddingProviderType, VectorStoreType
from app.core.logger import get_logger
from app.database.session import get_session_factory
from app.infrastructure.knowledge.embeddings.factory import (
    build_azure_openai_embedding,
    build_bge_embedding,
    build_nomic_embedding,
    build_openai_embedding,
    build_voyageai_embedding,
)
from app.infrastructure.knowledge.vector_stores.milvus_store import build_milvus_store
from app.infrastructure.knowledge.vector_stores.pgvector_store import PgVectorStore
from app.infrastructure.knowledge.vector_stores.pinecone_store import build_pinecone_store
from app.infrastructure.knowledge.vector_stores.qdrant_store import build_qdrant_store
from app.infrastructure.knowledge.vector_stores.weaviate_store import build_weaviate_store
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.retrieval.vector_store import VectorStore

logger = get_logger(__name__)

_EMBEDDING_BUILDERS = {
    EmbeddingProviderType.OPENAI: build_openai_embedding,
    EmbeddingProviderType.VOYAGEAI: build_voyageai_embedding,
    EmbeddingProviderType.NOMIC: build_nomic_embedding,
    EmbeddingProviderType.AZURE_OPENAI: build_azure_openai_embedding,
    EmbeddingProviderType.BGE: build_bge_embedding,
}

_VECTOR_BUILDERS = {
    VectorStoreType.QDRANT: build_qdrant_store,
    VectorStoreType.PINECONE: build_pinecone_store,
    VectorStoreType.WEAVIATE: build_weaviate_store,
    VectorStoreType.MILVUS: build_milvus_store,
}


def build_embedding_provider() -> EmbeddingProvider | None:
    provider_id = settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER
    if not provider_id:
        return None
    builder = _EMBEDDING_BUILDERS.get(provider_id)
    if builder is None:
        raise ValueError(f"Unsupported embedding provider: {provider_id}")
    return builder()


def build_vector_store() -> VectorStore | None:
    store_id = settings.KNOWLEDGE_DEFAULT_VECTOR_STORE
    if not store_id:
        return None
    if store_id == VectorStoreType.PGVECTOR:
        factory = get_session_factory()
        if factory is None:
            raise RuntimeError("DATABASE_URL required for pgvector store")
        return PgVectorStore(factory)
    builder = _VECTOR_BUILDERS.get(store_id)
    if builder is None:
        raise ValueError(f"Unsupported vector store: {store_id}")
    return builder()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider | None:
    return build_embedding_provider()


@lru_cache
def get_vector_store() -> VectorStore | None:
    return build_vector_store()


async def validate_knowledge_platform() -> None:
    """Fail fast when knowledge providers are misconfigured."""
    if not settings.KNOWLEDGE_REQUIRE_PROVIDERS and not (
        settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER or settings.KNOWLEDGE_DEFAULT_VECTOR_STORE
    ):
        logger.info("Knowledge providers not configured — ingestion will skip embedding/vector stages")
        return

    if settings.KNOWLEDGE_REQUIRE_PROVIDERS or settings.is_production:
        if not settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER:
            raise RuntimeError("KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER must be set in production")
        if not settings.KNOWLEDGE_DEFAULT_VECTOR_STORE:
            raise RuntimeError("KNOWLEDGE_DEFAULT_VECTOR_STORE must be set in production")

    embedder = get_embedding_provider()
    store = get_vector_store()

    if settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER and embedder is None:
        raise RuntimeError("Failed to build embedding provider")

    if settings.KNOWLEDGE_DEFAULT_VECTOR_STORE and store is None:
        raise RuntimeError("Failed to build vector store")

    if embedder is not None:
        logger.info("Validating embedding provider", extra_fields={"provider": embedder.provider_name})
        await embedder.validate_connection()

    if store is not None:
        logger.info("Validating vector store", extra_fields={"store": store.store_name})
        await store.validate_connection()

    logger.info(
        "Knowledge platform validated",
        extra_fields={
            "embedding_provider": embedder.provider_name if embedder else None,
            "vector_store": store.store_name if store else None,
        },
    )
