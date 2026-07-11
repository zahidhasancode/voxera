"""Document parser abstractions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.enums import KnowledgeSourceType


@dataclass
class ParsedPage:
    page_number: int
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Normalized output from any document parser."""

    text: str
    pages: list[ParsedPage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    language: str | None = None


class DocumentParser(ABC):
    """Port for parsing uploaded files or fetched web content."""

    @property
    @abstractmethod
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        raise NotImplementedError

    @abstractmethod
    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        raise NotImplementedError

    @abstractmethod
    async def parse_url(self, url: str) -> ParsedDocument:
        raise NotImplementedError

    def supports(self, source_type: KnowledgeSourceType) -> bool:
        return source_type in self.supported_types
