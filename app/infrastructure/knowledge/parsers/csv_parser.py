"""CSV / FAQ document parser."""

import csv
import io
from pathlib import Path

from app.core.enums import KnowledgeSourceType
from app.knowledge.parser.base import DocumentParser, ParsedDocument, ParsedPage


class CsvDocumentParser(DocumentParser):
    @property
    def supported_types(self) -> frozenset[KnowledgeSourceType]:
        return frozenset({KnowledgeSourceType.CSV_FAQ})

    async def parse_file(self, file_path: str, *, source_type: KnowledgeSourceType) -> ParsedDocument:
        path = Path(file_path)
        raw = path.read_bytes()
        text_content = raw.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            return ParsedDocument(text="", metadata={"filename": path.name})

        header = rows[0]
        question_idx = self._column_index(header, ("question", "q", "prompt"))
        answer_idx = self._column_index(header, ("answer", "a", "response"))
        sections: list[str] = []
        for row in rows[1:]:
            if not any(cell.strip() for cell in row):
                continue
            if question_idx is not None and answer_idx is not None and len(row) > max(question_idx, answer_idx):
                sections.append(f"Q: {row[question_idx].strip()}\nA: {row[answer_idx].strip()}")
            else:
                sections.append(" | ".join(cell.strip() for cell in row if cell.strip()))
        text = "\n\n".join(sections)
        return ParsedDocument(
            text=text,
            pages=[ParsedPage(page_number=1, content=text, metadata={"row_count": len(rows) - 1})],
            metadata={"filename": path.name, "source_type": source_type.value, "format": "csv_faq"},
        )

    async def parse_url(self, url: str) -> ParsedDocument:
        raise NotImplementedError("CSV URL parsing is not supported")

    def _column_index(self, header: list[str], candidates: tuple[str, ...]) -> int | None:
        normalized = [h.strip().lower() for h in header]
        for candidate in candidates:
            if candidate in normalized:
                return normalized.index(candidate)
        return None
