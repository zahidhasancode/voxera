"""Qdrant REST vector store implementation."""

from __future__ import annotations

from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    def __init__(self, *, url: str, api_key: str | None = None) -> None:
        self._url = url.rstrip("/")
        self._api_key = api_key

    @property
    def store_name(self) -> str:
        return "qdrant"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["api-key"] = self._api_key
        return headers

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._url}/collections", headers=self._headers())
            response.raise_for_status()

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self._url}/collections/{namespace}",
                headers=self._headers(),
                json={"vectors": {"size": dimensions, "distance": "Cosine"}},
            )
            if response.status_code not in (200, 201, 409):
                response.raise_for_status()

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        points = []
        ids: list[str] = []
        for record in records:
            point_id = record.id or str(uuid4())
            ids.append(point_id)
            points.append({"id": point_id, "vector": record.vector, "payload": record.metadata})
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(
                f"{self._url}/collections/{namespace}/points",
                headers=self._headers(),
                json={"points": points},
            )
            response.raise_for_status()
        return ids

    async def delete(self, namespace: str, ids: list[str]) -> int:
        if not ids:
            return 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._url}/collections/{namespace}/points/delete",
                headers=self._headers(),
                json={"points": ids},
            )
            response.raise_for_status()
        return len(ids)

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        payload = {
            "vector": request.query_vector,
            "limit": request.top_k,
            "score_threshold": request.min_score,
            "with_payload": True,
        }
        if request.metadata_filter:
            payload["filter"] = {
                "must": [
                    {"key": k, "match": {"value": v}} for k, v in request.metadata_filter.items()
                ]
            }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._url}/collections/{request.namespace}/points/search",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return [
            VectorSearchResult(
                id=str(item["id"]),
                score=float(item["score"]),
                metadata=item.get("payload") or {},
            )
            for item in data.get("result", [])
        ]

    async def delete_namespace(self, namespace: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self._url}/collections/{namespace}",
                headers=self._headers(),
            )
            if response.status_code not in (200, 404):
                response.raise_for_status()


def build_qdrant_store() -> QdrantVectorStore:
    if not settings.QDRANT_URL:
        raise ValueError("QDRANT_URL is required for Qdrant vector store")
    return QdrantVectorStore(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
