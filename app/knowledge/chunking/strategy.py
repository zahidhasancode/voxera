"""Document chunking strategy."""

import re

from app.core.enums import ChunkStrategyType
from app.core.logger import get_logger
from app.knowledge.chunking.models import ChunkConfig, TextChunk

logger = get_logger(__name__)

_SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class ChunkingStrategy:
    """Configurable text chunking for knowledge ingestion."""

    def __init__(self, config: ChunkConfig | None = None) -> None:
        self._config = config or ChunkConfig()

    @property
    def config(self) -> ChunkConfig:
        return self._config

    def chunk_text(
        self,
        text: str,
        *,
        base_metadata: dict | None = None,
    ) -> list[TextChunk]:
        if not text or not text.strip():
            return []

        strategy = self._config.strategy
        if strategy == ChunkStrategyType.SENTENCE:
            chunks = self._chunk_by_sentences(text, base_metadata)
        elif strategy == ChunkStrategyType.MARKDOWN:
            chunks = self._chunk_markdown(text, base_metadata)
        elif strategy == ChunkStrategyType.TOKEN:
            chunks = self._chunk_by_tokens(text, base_metadata)
        elif strategy == ChunkStrategyType.SEMANTIC:
            chunks = self._chunk_recursive(text, base_metadata, separator="\n\n")
        else:
            chunks = self._chunk_recursive(text, base_metadata, separator=self._config.separator)

        logger.debug(
            "Text chunked",
            extra_fields={
                "chunk_count": len(chunks),
                "strategy": strategy.value,
                "chunk_size": self._config.chunk_size,
            },
        )
        return chunks

    def _chunk_recursive(
        self,
        text: str,
        base_metadata: dict | None,
        *,
        separator: str,
    ) -> list[TextChunk]:
        cfg = self._config
        chunks: list[TextChunk] = []
        parts = text.split(separator) if cfg.preserve_sections else [text]
        buffer = ""
        chunk_number = 0

        for part in parts:
            candidate = f"{buffer}{separator}{part}".strip() if buffer else part.strip()
            if len(candidate) <= cfg.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(self._make_chunk(buffer, chunk_number, base_metadata))
                chunk_number += 1
                overlap = buffer[-cfg.chunk_overlap :] if cfg.chunk_overlap else ""
                buffer = f"{overlap}{separator}{part}".strip() if overlap else part.strip()
            else:
                buffer = self._split_oversized(part, chunks, chunk_number, base_metadata)
                chunk_number = len(chunks)

        if buffer.strip():
            chunks.append(self._make_chunk(buffer.strip(), chunk_number, base_metadata))
        return chunks

    def _chunk_by_sentences(self, text: str, base_metadata: dict | None) -> list[TextChunk]:
        sentences = _SENTENCE_PATTERN.split(text.strip())
        chunks: list[TextChunk] = []
        buffer = ""
        chunk_number = 0
        for sentence in sentences:
            candidate = f"{buffer} {sentence}".strip() if buffer else sentence.strip()
            if len(candidate) <= self._config.chunk_size:
                buffer = candidate
                continue
            if buffer:
                chunks.append(self._make_chunk(buffer, chunk_number, base_metadata))
                chunk_number += 1
            buffer = sentence.strip()
        if buffer:
            chunks.append(self._make_chunk(buffer, chunk_number, base_metadata))
        return chunks

    def _chunk_markdown(self, text: str, base_metadata: dict | None) -> list[TextChunk]:
        sections: list[tuple[str | None, str]] = []
        current_heading: str | None = None
        current_lines: list[str] = []

        for line in text.splitlines():
            match = _MARKDOWN_HEADING.match(line)
            if match:
                if current_lines:
                    sections.append((current_heading, "\n".join(current_lines).strip()))
                current_heading = match.group(2).strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            sections.append((current_heading, "\n".join(current_lines).strip()))

        chunks: list[TextChunk] = []
        chunk_number = 0
        for heading, section_text in sections:
            if not section_text:
                continue
            metadata = dict(base_metadata or {})
            if heading:
                metadata["heading"] = heading
            section_chunks = self._chunk_recursive(section_text, metadata, separator="\n\n")
            for chunk in section_chunks:
                chunk.chunk_number = chunk_number
                metadata = dict(chunk.metadata or {})
                metadata["chunk_number"] = chunk_number
                chunk.metadata = metadata
                chunks.append(chunk)
                chunk_number += 1
        return chunks or self._chunk_recursive(text, base_metadata, separator="\n\n")

    def _chunk_by_tokens(self, text: str, base_metadata: dict | None) -> list[TextChunk]:
        max_tokens = self._config.maximum_tokens or 256
        words = text.split()
        chunks: list[TextChunk] = []
        chunk_number = 0
        for index in range(0, len(words), max_tokens - min(32, max_tokens // 4)):
            piece_words = words[index : index + max_tokens]
            if not piece_words:
                continue
            content = " ".join(piece_words)
            chunks.append(
                TextChunk(
                    chunk_number=chunk_number,
                    content=content,
                    char_count=len(content),
                    token_count=len(piece_words),
                    metadata={**(base_metadata or {}), "chunk_number": chunk_number},
                )
            )
            chunk_number += 1
        return chunks

    def _split_oversized(
        self,
        text: str,
        chunks: list[TextChunk],
        start_number: int,
        base_metadata: dict | None,
    ) -> str:
        cfg = self._config
        remaining = text
        chunk_number = start_number
        while len(remaining) > cfg.chunk_size:
            piece = remaining[: cfg.chunk_size]
            chunks.append(self._make_chunk(piece, chunk_number, base_metadata))
            chunk_number += 1
            remaining = remaining[cfg.chunk_size - cfg.chunk_overlap :]
        return remaining

    def _make_chunk(
        self,
        content: str,
        chunk_number: int,
        base_metadata: dict | None,
    ) -> TextChunk:
        metadata = dict(base_metadata or {})
        metadata.update({"chunk_number": chunk_number})
        if self._config.language:
            metadata["language"] = self._config.language
        token_count = len(content.split())
        if self._config.maximum_tokens is not None:
            token_count = min(token_count, self._config.maximum_tokens)
        return TextChunk(
            chunk_number=chunk_number,
            content=content,
            char_count=len(content),
            token_count=token_count,
            metadata=metadata,
        )
