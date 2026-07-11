"""HTML document parser."""

from pathlib import Path

from bs4 import BeautifulSoup

from app.core.enums import KnowledgeSourceType
from app.knowledge.parser.base import DocumentParser, ParsedDocument, ParsedPage


class HtmlDocumentParser(DocumentParser):
    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return frozenset({KnowledgeSourceType.HTML})

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        path = Path(file_path)
        html = path.read_text(encoding="utf-8", errors="replace")
        return self._parse_html(html, metadata={"filename": path.name, "source_type": source_type.value})

    async def parse_url(self, url: str) -> ParsedDocument:
        raise NotImplementedError("Use WebsiteDocumentParser for remote HTML")

    def _parse_html(self, html: str, *, metadata: dict) -> ParsedDocument:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        text = soup.get_text(separator="\n", strip=True)
        page_metadata = dict(metadata)
        if title:
            page_metadata["title"] = title
        return ParsedDocument(
            text=text,
            pages=[ParsedPage(page_number=1, content=text, metadata=page_metadata)],
            metadata=page_metadata,
        )
