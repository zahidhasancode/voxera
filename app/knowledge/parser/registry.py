"""Parser registry — maps source types to parser implementations."""

from app.core.enums import KnowledgeSourceType
from app.core.exceptions import NotFoundError
from app.knowledge.parser.base import DocumentParser


class ParserRegistry:
    """Resolves the appropriate DocumentParser for a source type."""

    def __init__(self) -> None:
        self._parsers: list[DocumentParser] = []

    def register(self, parser: DocumentParser) -> None:
        self._parsers.append(parser)

    def resolve(self, source_type: KnowledgeSourceType) -> DocumentParser:
        for parser in self._parsers:
            if parser.supports(source_type):
                return parser
        raise NotFoundError(f"No parser registered for source type: {source_type.value}")

    @property
    def registered_types(self) -> set[KnowledgeSourceType]:
        types: set[KnowledgeSourceType] = set()
        for parser in self._parsers:
            types.update(parser.supported_types)
        return types
