"""PDF document parser."""

from pathlib import Path

from pypdf import PdfReader

from app.core.enums import KnowledgeSourceType
from app.knowledge.parser.base import DocumentParser, ParsedDocument, ParsedPage


class PdfDocumentParser(DocumentParser):
    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return frozenset({KnowledgeSourceType.PDF})

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        path = Path(file_path)
        reader = PdfReader(str(path))
        pages: list[ParsedPage] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(
                ParsedPage(
                    page_number=index,
                    content=text,
                    metadata={"page": index},
                )
            )
        combined = "\n\n".join(p.content for p in pages if p.content.strip())
        return ParsedDocument(
            text=combined,
            pages=pages,
            metadata={"filename": path.name, "page_count": len(pages), "source_type": source_type.value},
        )

    async def parse_url(self, url: str) -> ParsedDocument:
        raise NotImplementedError("PDF URL parsing is not supported")
