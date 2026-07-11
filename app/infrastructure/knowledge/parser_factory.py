"""Build default parser registry for knowledge ingestion."""

from app.core.enums import KnowledgeSourceType
from app.infrastructure.knowledge.parsers.csv_parser import CsvDocumentParser
from app.infrastructure.knowledge.parsers.docx_parser import DocxDocumentParser
from app.infrastructure.knowledge.parsers.html_parser import HtmlDocumentParser
from app.infrastructure.knowledge.parsers.pdf_parser import PdfDocumentParser
from app.infrastructure.knowledge.parsers.plain_text_parser import PlainTextDocumentParser
from app.infrastructure.knowledge.parsers.unsupported_parser import UnsupportedDocumentParser
from app.infrastructure.knowledge.parsers.website_parser import WebsiteDocumentParser
from app.knowledge.parser.registry import ParserRegistry


def build_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(PlainTextDocumentParser())
    registry.register(PdfDocumentParser())
    registry.register(DocxDocumentParser())
    registry.register(CsvDocumentParser())
    registry.register(HtmlDocumentParser())
    registry.register(WebsiteDocumentParser())
    registry.register(
        UnsupportedDocumentParser(
            frozenset(
                {
                    KnowledgeSourceType.CONFLUENCE,
                    KnowledgeSourceType.NOTION,
                    KnowledgeSourceType.GOOGLE_DRIVE,
                    KnowledgeSourceType.SHAREPOINT,
                }
            )
        )
    )
    return registry
