"""Website fetch and HTML extraction parser."""

import httpx
from bs4 import BeautifulSoup

from app.core.enums import KnowledgeSourceType
from app.knowledge.parser.base import DocumentParser, ParsedDocument, ParsedPage


class WebsiteDocumentParser(DocumentParser):
    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return frozenset({KnowledgeSourceType.WEBSITE})

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        raise NotImplementedError("Website sources must use parse_url")

    async def parse_url(self, url: str) -> ParsedDocument:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "VOXERA-KnowledgeBot/1.0"})
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            html = response.text

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        text = soup.get_text(separator="\n", strip=True)
        metadata = {"url": url, "content_type": content_type, "source_type": KnowledgeSourceType.WEBSITE.value}
        if title:
            metadata["title"] = title
        return ParsedDocument(
            text=text,
            pages=[ParsedPage(page_number=1, content=text, metadata={"url": url})],
            metadata=metadata,
        )
