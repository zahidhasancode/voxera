"""Plain-text document parser for TXT and Markdown sources."""

from pathlib import Path

from app.core.enums import KnowledgeSourceType
from app.knowledge.parser.base import DocumentParser, ParsedDocument, ParsedPage


class PlainTextDocumentParser(DocumentParser):
    """Reads UTF-8 text files — no external dependencies."""

    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return frozenset({KnowledgeSourceType.TXT, KnowledgeSourceType.MD})

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="replace")
        return ParsedDocument(
            text=text,
            pages=[ParsedPage(page_number=1, content=text, metadata={"filename": path.name})],
            metadata={"filename": path.name, "source_type": source_type.value},
        )

    async def parse_url(self, url: str) -> ParsedDocument:
        raise NotImplementedError("URL parsing requires a website fetcher implementation")
