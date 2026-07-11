"""Pinecone REST vector store implementation."""

from __future__ import annotations

from uuid import uuid4

import httpx

from app.core.config import settings
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore


class PineconeVectorStore(VectorStore):
    def __init__(self, *, host: str, api_key: str) -> None:
        self._host = host.rstrip("/")
        if not self._host.startswith("http"):
            self._host = f"https://{self._host}"
        self._api_key = api_key

    @property
    def store_name(self) -> str:
        return "pinecone"

    def _headers(self) -> dict[str, str]:
        return {"Api-Key": self._api_key, "Content-Type": "application/json"}

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._host}/describe_index_stats",
                headers=self._headers(),
                json={},
            )
            response.raise_for_status()

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        return None

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        vectors = []
        ids: list[str] = []
        for record in records:
            vid = record.id or str(uuid4())
            ids.append(vid)
            meta = dict(record.metadata)
            meta["namespace"] = namespace
            vectors.append({"id": vid, "values": record.vector, "metadata": meta})
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._host}/vectors/upsert",
                headers=self._headers(),
                json={"vectors": vectors, "namespace": namespace},
            )
            response.raise_for_status()
        return ids

    async def delete(self, namespace: str, ids: list[str]) -> int:
        if not ids:
            return 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._host}/vectors/delete",
                headers=self._headers(),
                json={"ids": ids, "namespace": namespace},
            )
            response.raise_for_status()
        return len(ids)

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        filter_meta = request.metadata_filter or {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._host}/query",
                headers=self._headers(),
                json={
                    "vector": request.query_vector,
                    "topK": request.top_k,
                    "namespace": request.namespace,
                    "includeMetadata": True,
                    "filter": filter_meta or None,
                },
            )
            response.raise_for_status()
            data = response.json()
        matches = data.get("matches", [])
        return [
            VectorSearchResult(
                id=m["id"],
                score=float(m["score"]),
                metadata=m.get("metadata") or {},
            )
            for m in matches
            if float(m["score"]) >= request.min_score
        ]

    async def delete_namespace(self, namespace: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{self._host}/vectors/delete",
                headers=self._headers(),
                json={"deleteAll": True, "namespace": namespace},
            )


def build_pinecone_store() -> PineconeVectorStore:
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_HOST:
        raise ValueError("PINECONE_API_KEY and PINECONE_INDEX_HOST are required")
    return PineconeVectorStore(host=settings.PINECONE_INDEX_HOST, api_key=settings.PINECONE_API_KEY)
