"""Shared HTTP embedding provider base."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.knowledge.embeddings.provider import EmbeddingBatch, EmbeddingProvider, EmbeddingVector

logger = get_logger(__name__)


class HttpEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible HTTP embedding client with batching, retry, and cache hooks."""

    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        api_base: str,
        api_key: str | None,
        dimensions: int | None = None,
        batch_size: int | None = None,
        extra_headers: dict[str, str] | None = None,
        cache: Any | None = None,
        embeddings_path: str | None = None,
    ) -> None:
        self._provider_name = provider_name
        self._model_name = model_name
        self._api_base = api_base.rstrip("/")
        self._api_key = api_key
        self._dimensions = dimensions or settings.KNOWLEDGE_EMBEDDING_DIMENSIONS
        self._batch_size = batch_size or settings.KNOWLEDGE_EMBEDDING_BATCH_SIZE
        self._extra_headers = extra_headers or {}
        self._cache = cache
        self._embeddings_path = embeddings_path

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def validate_connection(self) -> None:
        await self.embed_query("health check")

    async def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        vectors: list[EmbeddingVector] = []
        for i in range(0, len(texts), self._batch_size):
            batch_texts = texts[i : i + self._batch_size]
            batch_vectors = await self._embed_batch(batch_texts, input_type="document")
            vectors.extend(batch_vectors)
        return EmbeddingBatch(vectors=vectors, model=self._model_name)

    async def embed_query(self, query: str) -> EmbeddingVector:
        vectors = await self._embed_batch([query], input_type="query")
        return vectors[0]

    async def _embed_batch(self, texts: list[str], *, input_type: str) -> list[EmbeddingVector]:
        results: list[EmbeddingVector] = []
        uncached: list[str] = []
        uncached_indices: list[int] = []

        for idx, text in enumerate(texts):
            cached = self._get_cached(text, input_type)
            if cached is not None:
                results.append((idx, cached))
            else:
                uncached.append(text)
                uncached_indices.append(idx)

        fetched: list[EmbeddingVector] = []
        if uncached:
            fetched = await self._request_embeddings(uncached, input_type=input_type)
            for text, vector in zip(uncached, fetched):
                self._set_cached(text, input_type, vector)

        # Merge in original order
        ordered: list[EmbeddingVector | None] = [None] * len(texts)
        for idx, vector in results:
            ordered[idx] = vector
        fetch_iter = iter(fetched)
        for idx in uncached_indices:
            ordered[idx] = next(fetch_iter)
        return [v for v in ordered if v is not None]

    async def _request_embeddings(self, texts: list[str], *, input_type: str) -> list[EmbeddingVector]:
        headers = {"Content-Type": "application/json", **self._extra_headers}
        if self._api_key and "api-key" not in headers:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {"input": texts if len(texts) > 1 else texts[0], "model": self._model_name}
        if self._dimensions and self._provider_name in {"openai", "azure_openai"}:
            payload["dimensions"] = self._dimensions

        path = self._embeddings_path or "/embeddings"
        if not path.startswith("/"):
            path = f"/{path}"
        url = f"{self._api_base}{path}"
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    items = sorted(data["data"], key=lambda x: x["index"])
                    return [
                        EmbeddingVector(
                            vector=item["embedding"],
                            model=self._model_name,
                            dimensions=len(item["embedding"]),
                            token_count=data.get("usage", {}).get("total_tokens"),
                        )
                        for item in items
                    ]
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Embedding request failed",
                    extra_fields={
                        "provider": self._provider_name,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Embedding provider {self._provider_name} failed: {last_error}")

    def _cache_key(self, text: str, input_type: str) -> str:
        digest = hashlib.sha256(f"{self._model_name}:{input_type}:{text}".encode()).hexdigest()
        return f"emb:{self._provider_name}:{digest}"

    def _get_cached(self, text: str, input_type: str) -> EmbeddingVector | None:
        if self._cache is None:
            return None
        return self._cache.get(self._cache_key(text, input_type))

    def _set_cached(self, text: str, input_type: str, vector: EmbeddingVector) -> None:
        if self._cache is None:
            return
        self._cache.set(self._cache_key(text, input_type), vector)
