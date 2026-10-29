"""Amazon Bedrock streaming LLM engine (Converse Stream API)."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import AsyncIterator, Optional, Sequence

from app.core.config import settings
from app.core.logger import get_logger
from app.llm.streaming_engine import LLMGenerationMetrics, StreamToken, StreamingLLMEngine

logger = get_logger(__name__)

_DONE = object()


class BedrockStreamingLLMEngine(StreamingLLMEngine):
    """Streams tokens from any Bedrock text model through ConverseStream.

    boto3 is synchronous, so the HTTP stream is read on a worker thread and handed to
    the event loop through a queue. Cancelling the consumer (barge-in) sets a stop flag
    and closes the stream, so the thread ends promptly.
    """

    def __init__(
        self,
        *,
        model_id: str | None = None,
        region: str | None = None,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        client=None,
    ) -> None:
        self._model_id = model_id or settings.BEDROCK_MODEL_ID
        self._region = region or settings.AWS_VOICE_REGION
        self._system_prompt = system_prompt or settings.VOICE_LLM_SYSTEM_PROMPT
        self._max_tokens = max_tokens or settings.VOICE_LLM_MAX_TOKENS
        self._client = client
        self._last_metrics = LLMGenerationMetrics()

    def _bedrock(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    async def validate_connection(self) -> None:
        import boto3

        control = boto3.client("bedrock", region_name=self._region)
        await asyncio.to_thread(control.list_foundation_models, byOutputModality="TEXT")

    def _messages(self, prompt: str, history: Optional[Sequence[dict]]) -> list[dict]:
        msgs = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in (history or [])
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]
        msgs.append({"role": "user", "content": [{"text": prompt or "(silence)"}]})
        return msgs

    async def stream(
        self,
        prompt: str,
        *,
        utterance_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        history: Optional[Sequence[dict]] = None,
    ) -> AsyncIterator[StreamToken]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()
        holder: dict = {}

        def worker() -> None:
            try:
                response = self._bedrock().converse_stream(
                    modelId=self._model_id,
                    system=[{"text": self._system_prompt}],
                    messages=self._messages(prompt, history),
                    inferenceConfig={"maxTokens": self._max_tokens},
                )
                holder["stream"] = response["stream"]
                for event in response["stream"]:
                    if stop.is_set():
                        break
                    text = event.get("contentBlockDelta", {}).get("delta", {}).get("text")
                    if text:
                        loop.call_soon_threadsafe(queue.put_nowait, text)
            except Exception as exc:  # surfaced to the consumer below
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _DONE)

        start = time.monotonic()
        first_token_time: float | None = None
        token_count = 0
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            while True:
                item = await queue.get()
                if item is _DONE:
                    break
                if isinstance(item, Exception):
                    raise item
                if first_token_time is None:
                    first_token_time = time.monotonic()
                yield StreamToken(token=item, token_index=token_count)
                token_count += 1
        except asyncio.CancelledError:
            logger.info("Bedrock LLM stream cancelled", extra_fields={"utterance_id": utterance_id, "tokens_emitted": token_count})
            raise
        finally:
            stop.set()
            stream = holder.get("stream")
            if stream is not None and hasattr(stream, "close"):
                try:
                    stream.close()
                except Exception as exc:  # closing an already finished stream
                    logger.debug("Bedrock stream close failed", extra_fields={"error": repr(exc)})
            end = time.monotonic()
            ttft = (first_token_time - start) * 1000.0 if first_token_time else 0.0
            total_ms = (end - start) * 1000.0
            self._last_metrics = LLMGenerationMetrics(
                time_to_first_token_ms=ttft,
                total_generation_ms=total_ms,
                token_count=token_count,
                tokens_per_second=token_count / (total_ms / 1000.0) if total_ms > 0 else 0.0,
            )

    def last_metrics(self) -> LLMGenerationMetrics:
        return self._last_metrics
