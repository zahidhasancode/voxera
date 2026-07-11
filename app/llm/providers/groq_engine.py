"""Groq OpenAI-compatible streaming LLM engine."""

from app.core.config import settings
from app.llm.providers.openai_engine import OpenAIStreamingLLMEngine


class GroqStreamingLLMEngine(OpenAIStreamingLLMEngine):
    def __init__(self, *, api_key: str, model: str | None = None) -> None:
        super().__init__(
            api_key=api_key,
            model=model or settings.GROQ_MODEL,
            api_base="https://api.groq.com/openai/v1",
        )
