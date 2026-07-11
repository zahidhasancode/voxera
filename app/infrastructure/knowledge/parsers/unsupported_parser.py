"""Stub parser for source types pending dedicated implementations."""

from app.core.enums import KnowledgeSourceType
from app.core.exceptions import DatabaseUnavailableError
from app.knowledge.parser.base import DocumentParser, ParsedDocument


class UnsupportedDocumentParser(DocumentParser):
    """Returns a clear error for source types without a registered parser."""

    def __init__(self, source_types: frozenset[KnowledgeSourceType]) -> None:
        self._types = source_types

    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return self._types

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        raise DatabaseUnavailableError(
            f"Parser for {source_type.value} is not yet implemented. "
            "Register a DocumentParser for this source type."
        )

    async def parse_url(self, url: str) -> ParsedDocument:
        raise DatabaseUnavailableError(
            "URL parsing is not implemented for this source type."
        )
