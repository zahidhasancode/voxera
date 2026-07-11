"""pgvector-backed vector store implementation."""

from __future__ import annotations

import json
import math
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.logger import get_logger
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore

logger = get_logger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class PgVectorStore(VectorStore):
    """PostgreSQL-backed vector storage using JSONB embeddings (pgvector-ready)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @property
    def store_name(self) -> str:
        return "pgvector"

    async def validate_connection(self) -> None:
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        # Namespaces are logical; table is shared with namespace column
        logger.debug(
            "pgvector namespace ready",
            extra_fields={"namespace": namespace, "dimensions": dimensions},
        )

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        ids: list[str] = []
        async with self._session_factory() as session:
            for record in records:
                vector_id = record.id or str(uuid4())
                await session.execute(
                    text(
                        """
                        INSERT INTO knowledge_vectors (id, namespace, vector_id, embedding, metadata, dimensions)
                        VALUES (:id, :namespace, :vector_id, :embedding::jsonb, :metadata::jsonb, :dimensions)
                        ON CONFLICT (namespace, vector_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            dimensions = EXCLUDED.dimensions,
                            updated_at = now()
                        """
                    ),
                    {
                        "id": str(uuid4()),
                        "namespace": namespace,
                        "vector_id": vector_id,
                        "embedding": json.dumps(record.vector),
                        "metadata": json.dumps(record.metadata),
                        "dimensions": len(record.vector),
                    },
                )
                ids.append(vector_id)
            await session.commit()
        return ids

    async def delete(self, namespace: str, ids: list[str]) -> int:
        if not ids:
            return 0
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    DELETE FROM knowledge_vectors
                    WHERE namespace = :namespace AND vector_id = ANY(:ids)
                    """
                ),
                {"namespace": namespace, "ids": ids},
            )
            await session.commit()
            return result.rowcount or 0

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT vector_id, embedding, metadata
                    FROM knowledge_vectors
                    WHERE namespace = :namespace
                    LIMIT 1000
                    """
                ),
                {"namespace": request.namespace},
            )
            rows = result.fetchall()

        scored: list[VectorSearchResult] = []
        for row in rows:
            vector = row.embedding if isinstance(row.embedding, list) else json.loads(row.embedding)
            metadata = row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata or "{}")
            if request.metadata_filter:
                if not all(metadata.get(k) == v for k, v in request.metadata_filter.items()):
                    continue
            score = _cosine_similarity(request.query_vector, vector)
            if score >= request.min_score:
                scored.append(VectorSearchResult(id=row.vector_id, score=score, metadata=metadata))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[: request.top_k]

    async def delete_namespace(self, namespace: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM knowledge_vectors WHERE namespace = :namespace"),
                {"namespace": namespace},
            )
            await session.commit()
