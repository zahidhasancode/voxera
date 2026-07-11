"""Query normalization for retrieval."""

import re
import unicodedata

from app.rag.interfaces.models import NormalizedQuery


class QueryNormalizer:
    """Deterministic query normalization before embedding."""

    _MULTI_SPACE = re.compile(r"\s+")
    _TRIM_PUNCT = re.compile(r"^[\s\W]+|[\s\W]+$")

    def normalize(self, query: str, *, detected_language: str | None = None) -> NormalizedQuery:
        text = unicodedata.normalize("NFKC", query.strip())
        text = self._MULTI_SPACE.sub(" ", text)
        text = self._TRIM_PUNCT.sub("", text)
        return NormalizedQuery(
            original=query,
            normalized=text,
            language=detected_language,
        )
