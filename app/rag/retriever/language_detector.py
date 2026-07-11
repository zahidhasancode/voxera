"""Language detection abstraction."""

import re
from abc import ABC, abstractmethod

from pydantic import Field

from app.core.schemas import SchemaBase


class LanguageDetectionResult(SchemaBase):
    language: str = Field(..., min_length=2, max_length=16)
    confidence: float = Field(..., ge=0.0, le=1.0)


class LanguageDetector(ABC):
    @abstractmethod
    async def detect(self, text: str) -> LanguageDetectionResult:
        raise NotImplementedError


class HeuristicLanguageDetector(LanguageDetector):
    """
    Lightweight heuristic detector for MVP.

    Replace with fastText / CLD3 / provider API in production.
    """

    _CYRILLIC = re.compile(r"[\u0400-\u04FF]")
    _CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff]")

    async def detect(self, text: str) -> LanguageDetectionResult:
        sample = text[:512]
        if self._CJK.search(sample):
            return LanguageDetectionResult(language="zh", confidence=0.7)
        if self._CYRILLIC.search(sample):
            return LanguageDetectionResult(language="ru", confidence=0.7)
        return LanguageDetectionResult(language="en", confidence=0.85)
