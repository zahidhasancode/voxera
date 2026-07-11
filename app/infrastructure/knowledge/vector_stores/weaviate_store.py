"""Weaviate GraphQL vector store implementation."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx

from app.core.config import settings
from app.knowledge.retrieval.vector_store import VectorRecord, VectorSearchRequest, VectorSearchResult, VectorStore


class WeaviateVectorStore(VectorStore):
    CLASS_NAME = "VoxeraKnowledgeChunk"

    def __init__(self, *, url: str, api_key: str | None = None) -> None:
        self._url = url.rstrip("/")
        self._api_key = api_key

    @property
    def store_name(self) -> str:
        return "weaviate"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._url}/v1/.well-known/ready", headers=self._headers())
            response.raise_for_status()

    async def create_namespace(self, namespace: str, *, dimensions: int) -> None:
        schema = {
            "class": self.CLASS_NAME,
            "vectorizer": "none",
            "properties": [
                {"name": "namespace", "dataType": ["text"]},
                {"name": "content_id", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["text"]},
            ],
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(f"{self._url}/v1/schema", headers=self._headers(), json=schema)

    async def insert(self, namespace: str, records: list[VectorRecord]) -> list[str]:
        ids: list[str] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for record in records:
                vid = record.id or str(uuid4())
                ids.append(vid)
                obj = {
                    "class": self.CLASS_NAME,
                    "id": vid,
                    "vector": record.vector,
                    "properties": {
                        "namespace": namespace,
                        "content_id": vid,
                        "metadata": json.dumps(record.metadata),
                    },
                }
                response = await client.post(
                    f"{self._url}/v1/objects",
                    headers=self._headers(),
                    json=obj,
                )
                response.raise_for_status()
        return ids

    async def delete(self, namespace: str, ids: list[str]) -> int:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for vid in ids:
                await client.delete(f"{self._url}/v1/objects/{vid}", headers=self._headers())
        return len(ids)

    async def search(self, request: VectorSearchRequest) -> list[VectorSearchResult]:
        gql = {
            "query": f"""
            {{
              Get {{
                {self.CLASS_NAME}(
                  nearVector: {{ vector: {json.dumps(request.query_vector)} }}
                  limit: {request.top_k}
                  where: {{ path: [\"namespace\"], operator: Equal, valueText: \"{request.namespace}\" }}
                ) {{
                  content_id
                  metadata
                  _additional {{ certainty }}
                }}
              }}
            }}
            """
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._url}/v1/graphql",
                headers=self._headers(),
                json=gql,
            )
            response.raise_for_status()
            data = response.json()
        items = data.get("data", {}).get("Get", {}).get(self.CLASS_NAME, [])
        results = []
        for item in items:
            score = float(item.get("_additional", {}).get("certainty") or 0)
            if score >= request.min_score:
                results.append(
                    VectorSearchResult(
                        id=item["content_id"],
                        score=score,
                        metadata=json.loads(item.get("metadata") or "{}"),
                    )
                )
        return results

    async def delete_namespace(self, namespace: str) -> None:
        gql = {
            "query": f"""
            mutation {{
              Delete {{
                {self.CLASS_NAME}(where: {{ path: [\"namespace\"], operator: Equal, valueText: \"{namespace}\" }}) {{
                  successful
                }}
              }}
            }}
            """
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(f"{self._url}/v1/graphql", headers=self._headers(), json=gql)


def build_weaviate_store() -> WeaviateVectorStore:
    if not settings.WEAVIATE_URL:
        raise ValueError("WEAVIATE_URL is required")
    return WeaviateVectorStore(url=settings.WEAVIATE_URL, api_key=settings.WEAVIATE_API_KEY)
