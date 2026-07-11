"""Knowledge subsystem dependency providers."""

from functools import lru_cache

from app.infrastructure.knowledge.parser_factory import build_parser_registry
from app.infrastructure.knowledge.registry import (
    get_embedding_provider as _get_embedding_provider,
    get_vector_store as _get_vector_store,
    validate_knowledge_platform,
)
from app.infrastructure.knowledge.storage import LocalKnowledgeFileStorage
from app.knowledge.embeddings.provider import EmbeddingProvider
from app.knowledge.retrieval.vector_store import VectorStore


@lru_cache
def get_embedding_provider() -> EmbeddingProvider | None:
    return _get_embedding_provider()


@lru_cache
def get_vector_store() -> VectorStore | None:
    return _get_vector_store()


@lru_cache
def get_file_storage() -> LocalKnowledgeFileStorage:
    return LocalKnowledgeFileStorage()


@lru_cache
def get_parser_registry():
    return build_parser_registry()


__all__ = [
    "get_embedding_provider",
    "get_vector_store",
    "get_file_storage",
    "get_parser_registry",
    "validate_knowledge_platform",
]
