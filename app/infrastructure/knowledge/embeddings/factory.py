"""Embedding provider factory functions."""

from app.core.config import settings
from app.core.enums import EmbeddingProviderType
from app.infrastructure.knowledge.cache import knowledge_cache
from app.infrastructure.knowledge.embeddings.http_embedding import HttpEmbeddingProvider
from app.knowledge.embeddings.provider import EmbeddingProvider


def build_openai_embedding() -> EmbeddingProvider:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required for OpenAI embedding provider")
    return HttpEmbeddingProvider(
        provider_name=EmbeddingProviderType.OPENAI,
        model_name=settings.KNOWLEDGE_EMBEDDING_MODEL,
        api_base=settings.OPENAI_API_BASE,
        api_key=settings.OPENAI_API_KEY,
        dimensions=settings.KNOWLEDGE_EMBEDDING_DIMENSIONS,
        cache=knowledge_cache,
    )


def build_voyageai_embedding() -> EmbeddingProvider:
    if not settings.VOYAGE_API_KEY:
        raise ValueError("VOYAGE_API_KEY is required for VoyageAI embedding provider")
    return HttpEmbeddingProvider(
        provider_name=EmbeddingProviderType.VOYAGEAI,
        model_name=settings.KNOWLEDGE_EMBEDDING_MODEL,
        api_base=settings.VOYAGE_API_BASE,
        api_key=settings.VOYAGE_API_KEY,
        cache=knowledge_cache,
    )


def build_nomic_embedding() -> EmbeddingProvider:
    if not settings.NOMIC_API_KEY:
        raise ValueError("NOMIC_API_KEY is required for Nomic embedding provider")
    return HttpEmbeddingProvider(
        provider_name=EmbeddingProviderType.NOMIC,
        model_name=settings.KNOWLEDGE_EMBEDDING_MODEL or "nomic-embed-text-v1.5",
        api_base=settings.NOMIC_API_BASE,
        api_key=settings.NOMIC_API_KEY,
        cache=knowledge_cache,
    )


def build_azure_openai_embedding() -> EmbeddingProvider:
    if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_API_KEY:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required")
    deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT or settings.KNOWLEDGE_EMBEDDING_MODEL
    api_base = f"{settings.AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{deployment}"
    return HttpEmbeddingProvider(
        provider_name=EmbeddingProviderType.AZURE_OPENAI,
        model_name=deployment,
        api_base=api_base,
        api_key=settings.AZURE_OPENAI_API_KEY,
        dimensions=settings.KNOWLEDGE_EMBEDDING_DIMENSIONS,
        extra_headers={"api-key": settings.AZURE_OPENAI_API_KEY},
        embeddings_path=f"/embeddings?api-version={settings.AZURE_OPENAI_API_VERSION}",
        cache=knowledge_cache,
    )


def build_bge_embedding() -> EmbeddingProvider:
    if not settings.BGE_EMBEDDING_URL:
        raise ValueError("BGE_EMBEDDING_URL is required for BGE embedding provider")
    return HttpEmbeddingProvider(
        provider_name=EmbeddingProviderType.BGE,
        model_name=settings.KNOWLEDGE_EMBEDDING_MODEL or "bge-large-en-v1.5",
        api_base=settings.BGE_EMBEDDING_URL.rstrip("/"),
        api_key=settings.BGE_API_KEY,
        cache=knowledge_cache,
    )
