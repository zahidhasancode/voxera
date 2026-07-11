"""Provider registry tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.enums import EmbeddingProviderType, VectorStoreType
from app.infrastructure.knowledge.registry import build_embedding_provider, build_vector_store


def test_build_openai_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER",
        EmbeddingProviderType.OPENAI,
    )
    monkeypatch.setattr("app.infrastructure.knowledge.registry.settings.OPENAI_API_KEY", None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_embedding_provider()


def test_build_pgvector_requires_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_VECTOR_STORE",
        VectorStoreType.PGVECTOR,
    )
    monkeypatch.setattr("app.infrastructure.knowledge.registry.get_session_factory", lambda: None)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_vector_store()


@pytest.mark.asyncio
async def test_validate_knowledge_platform_skips_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.infrastructure.knowledge.registry import validate_knowledge_platform

    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_REQUIRE_PROVIDERS",
        False,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER",
        None,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_VECTOR_STORE",
        None,
    )
    await validate_knowledge_platform()


@pytest.mark.asyncio
async def test_validate_knowledge_platform_checks_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.infrastructure.knowledge.registry import validate_knowledge_platform

    mock_embedder = AsyncMock()
    mock_embedder.provider_name = "openai"
    mock_embedder.validate_connection = AsyncMock()
    mock_store = AsyncMock()
    mock_store.store_name = "pgvector"
    mock_store.validate_connection = AsyncMock()

    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_REQUIRE_PROVIDERS",
        True,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_EMBEDDING_PROVIDER",
        EmbeddingProviderType.OPENAI,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.settings.KNOWLEDGE_DEFAULT_VECTOR_STORE",
        VectorStoreType.PGVECTOR,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.get_embedding_provider",
        lambda: mock_embedder,
    )
    monkeypatch.setattr(
        "app.infrastructure.knowledge.registry.get_vector_store",
        lambda: mock_store,
    )
    await validate_knowledge_platform()
    mock_embedder.validate_connection.assert_awaited_once()
    mock_store.validate_connection.assert_awaited_once()
