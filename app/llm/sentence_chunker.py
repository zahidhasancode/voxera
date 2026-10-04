"""Cut a stream of LLM tokens into speakable segments.

Speech can start as soon as the first sentence is complete, so the user does
not wait for the whole answer. Segments end at sentence punctuation followed by
whitespace; a long clause is cut at a comma or semicolon so a rambling sentence
does not delay speech either.
"""

from __future__ import annotations

_SENTENCE_END = ".!?…"
_CLAUSE_END = ",;:—"
_ABBREVIATIONS = (
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", "vs.", "etc.", "e.g.", "i.e.", "no.",
)


class SentenceChunker:
    """Incremental sentence segmentation for streamed text."""

    def __init__(self, *, min_chars: int = 12, soft_limit_chars: int = 90) -> None:
        self._min_chars = min_chars
        self._soft_limit = soft_limit_chars
        self._buffer = ""

    def feed(self, token: str) -> list[str]:
        """Add a token; return the segments that are now complete."""
        if not token:
            return []
        self._buffer += token
        segments: list[str] = []
        while True:
            cut = self._find_cut()
            if cut is None:
                break
            segment, self._buffer = self._buffer[:cut].strip(), self._buffer[cut:]
            if segment:
                segments.append(segment)
        return segments

    def flush(self) -> str | None:
        """Return whatever text is left (call when the stream ends)."""
        rest, self._buffer = self._buffer.strip(), ""
        return rest or None

    def _find_cut(self) -> int | None:
        text = self._buffer
        for i, ch in enumerate(text):
            if ch == "\n" and text[:i].strip():
                return i + 1
            if ch not in _SENTENCE_END:
                continue
            nxt = i + 1
            if nxt >= len(text):
                return None  # wait: the next token may continue "3.5" or "..."
            if not text[nxt].isspace():
                continue
            head = text[:nxt]
            if len(head.strip()) < self._min_chars:
                continue
            if head.rstrip().lower().endswith(_ABBREVIATIONS):
                continue
            return nxt
        if len(text) >= self._soft_limit:
            for i in range(len(text) - 2, self._min_chars, -1):
                if text[i] in _CLAUSE_END and text[i + 1].isspace():
                    return i + 1
        return None
