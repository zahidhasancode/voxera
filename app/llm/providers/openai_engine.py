"""OpenAI Chat Completions streaming LLM engine."""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncIterator, Optional

import httpx

from app.core.config import settings
from app.core.logger import get_logger
from app.llm.streaming_engine import LLMGenerationMetrics, StreamToken, StreamingLLMEngine

logger = get_logger(__name__)


class OpenAIStreamingLLMEngine(StreamingLLMEngine):
    """Streams tokens from OpenAI-compatible chat completions API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        api_base: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model or settings.VOICE_LLM_MODEL
        self._api_base = (api_base or settings.OPENAI_API_BASE).rstrip("/")
        self._system_prompt = system_prompt or settings.VOICE_LLM_SYSTEM_PROMPT
        self._max_tokens = max_tokens or settings.VOICE_LLM_MAX_TOKENS
        self._extra_headers = extra_headers or {}
        self._last_metrics = LLMGenerationMetrics()

    async def validate_connection(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self._api_base}/models",
                headers=self._headers(),
            )
            response.raise_for_status()

    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[StreamToken]:
        start = time.monotonic()
        first_token_time: float | None = None
        token_count = 0
        payload = {
            "model": self._model,
            "stream": True,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt or "(silence)"},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.VOICE_LLM_TIMEOUT_SECONDS) as client:
                async with client.stream(
                    "POST",
                    f"{self._api_base}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        token = delta.get("content")
                        if not token:
                            continue
                        if first_token_time is None:
                            first_token_time = time.monotonic()
                        yield StreamToken(token=token, token_index=token_count)
                        token_count += 1
        except asyncio.CancelledError:
            logger.info(
                "OpenAI LLM stream cancelled",
                extra_fields={"utterance_id": utterance_id, "tokens_emitted": token_count},
            )
            raise
        finally:
            end = time.monotonic()
            ttft = (first_token_time - start) * 1000.0 if first_token_time else 0.0
            total_ms = (end - start) * 1000.0
            tps = token_count / (total_ms / 1000.0) if total_ms > 0 else 0.0
            self._last_metrics = LLMGenerationMetrics(
                time_to_first_token_ms=ttft,
                total_generation_ms=total_ms,
                token_count=token_count,
                tokens_per_second=tps,
            )

    def last_metrics(self) -> LLMGenerationMetrics:
        return self._last_metrics

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        if "api-key" in self._extra_headers:
            headers.pop("Authorization", None)
        return headers
