"""Milvus REST vector store implementation."""

from __future__ import annotations

from uuid import uuid4

import httpx

from app.core.config import settings
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore


class MilvusVectorStore(VectorStore):
    def __init__(self, *, uri: str, token: str | None, collection: str) -> None:
        self._uri = uri.rstrip("/")
        self._token = token
        self._collection = collection

    @property
    def store_name(self) -> str:
        return "milvus"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._uri}/v2/vectordb/collections/list", headers=self._headers())
            response.raise_for_status()

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{self._uri}/v2/vectordb/collections/create",
                headers=self._headers(),
                json={
                    "collectionName": self._collection,
                    "dimension": dimensions,
                    "metricType": "COSINE",
                },
            )

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        ids: list[str] = []
        data = []
        for record in records:
            vid = record.id or str(uuid4())
            ids.append(vid)
            data.append({"id": vid, "vector": record.vector, "namespace": namespace, **record.metadata})
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._uri}/v2/vectordb/entities/insert",
                headers=self._headers(),
                json={"collectionName": self._collection, "data": data},
            )
            response.raise_for_status()
        return ids

    async def delete(self, namespace: str, ids: list[str]) -> int:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._uri}/v2/vectordb/entities/delete",
                headers=self._headers(),
                json={"collectionName": self._collection, "ids": ids},
            )
            response.raise_for_status()
        return len(ids)

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._uri}/v2/vectordb/entities/search",
                headers=self._headers(),
                json={
                    "collectionName": self._collection,
                    "vector": request.query_vector,
                    "limit": request.top_k,
                    "filter": f'namespace == "{request.namespace}"',
                },
            )
            response.raise_for_status()
            payload = response.json()
        return [
            VectorSearchResult(
                id=str(item.get("id")),
                score=float(item.get("score", 0)),
                metadata={k: v for k, v in item.items() if k not in {"id", "vector", "score"}},
            )
            for item in payload.get("data", [])
            if float(item.get("score", 0)) >= request.min_score
        ]

    async def delete_namespace(self, namespace: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{self._uri}/v2/vectordb/entities/delete",
                headers=self._headers(),
                json={
                    "collectionName": self._collection,
                    "filter": f'namespace == "{namespace}"',
                },
            )


def build_milvus_store() -> MilvusVectorStore:
    if not settings.MILVUS_URI:
        raise ValueError("MILVUS_URI is required")
    return MilvusVectorStore(
        uri=settings.MILVUS_URI,
        token=settings.MILVUS_TOKEN,
        collection=settings.MILVUS_COLLECTION,
    )
