"""Document upload validation for knowledge ingestion."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.enums import KnowledgeSourceType

_MAGIC_SIGNATURES: dict[KnowledgeSourceType, bytes] = {
    KnowledgeSourceType.PDF: b"%PDF",
    KnowledgeSourceType.DOCX: b"PK\x03\x04",
}

_EXTENSION_MAP: dict[str, KnowledgeSourceType] = {
    ".pdf": KnowledgeSourceType.PDF,
    ".docx": KnowledgeSourceType.DOCX,
    ".txt": KnowledgeSourceType.TXT,
    ".md": KnowledgeSourceType.MD,
    ".markdown": KnowledgeSourceType.MD,
    ".csv": KnowledgeSourceType.CSV_FAQ,
    ".html": KnowledgeSourceType.HTML,
    ".htm": KnowledgeSourceType.HTML,
}

_SUSPICIOUS_PATTERNS = (
    re.compile(r"<\s*script\b", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
)


@dataclass
class DocumentValidationResult:
    file_hash: str
    detected_type: KnowledgeSourceType | None
    encoding: str | None = None


class DocumentValidationError(ValueError):
    """Raised when an upload fails validation."""


class DocumentValidator:
    """Validates file type, size, encoding, corruption, and basic safety."""

    def validate_upload(
        self,
        *,
        filename: str,
        content: bytes,
        declared_type: KnowledgeSourceType,
        content_type: str | None = None,
    ) -> DocumentValidationResult:
        self._validate_filename(filename)
        self._validate_size(content)
        self._validate_not_empty(content)

        extension_type = self._type_from_extension(filename)
        if extension_type and extension_type != declared_type:
            raise DocumentValidationError(
                f"File extension does not match declared source type {declared_type.value}"
            )

        self._validate_magic_bytes(content, declared_type)
        encoding = self._validate_text_encoding(content, declared_type)
        self._scan_for_suspicious_content(content, declared_type)

        file_hash = hashlib.sha256(content).hexdigest()
        return DocumentValidationResult(
            file_hash=file_hash,
            detected_type=extension_type or declared_type,
            encoding=encoding,
        )

    def _validate_filename(self, filename: str) -> None:
        name = Path(filename).name
        if not name or name in {".", ".."}:
            raise DocumentValidationError("Invalid filename")
        if ".." in filename or filename.startswith("/") or "\\" in filename:
            raise DocumentValidationError("Path traversal detected in filename")
        if not settings.knowledge_allowed_extensions:
            return
        suffix = Path(name).suffix.lower().lstrip(".")
        if suffix and suffix not in settings.knowledge_allowed_extensions:
            raise DocumentValidationError(f"File extension .{suffix} is not allowed")

    def _validate_size(self, content: bytes) -> None:
        if len(content) > settings.KNOWLEDGE_MAX_UPLOAD_BYTES:
            raise DocumentValidationError(
                f"File exceeds maximum upload size of {settings.KNOWLEDGE_MAX_UPLOAD_BYTES} bytes"
            )

    def _validate_not_empty(self, content: bytes) -> None:
        if not content:
            raise DocumentValidationError("Empty file uploads are not allowed")

    def _type_from_extension(self, filename: str) -> KnowledgeSourceType | None:
        return _EXTENSION_MAP.get(Path(filename).suffix.lower())

    def _validate_magic_bytes(self, content: bytes, declared_type: KnowledgeSourceType) -> None:
        expected = _MAGIC_SIGNATURES.get(declared_type)
        if expected and not content.startswith(expected):
            raise DocumentValidationError(
                f"File content does not match declared type {declared_type.value}"
            )

    def _validate_text_encoding(self, content: bytes, declared_type: KnowledgeSourceType) -> str | None:
        if declared_type not in {
            KnowledgeSourceType.TXT,
            KnowledgeSourceType.MD,
            KnowledgeSourceType.CSV_FAQ,
            KnowledgeSourceType.HTML,
        }:
            return None
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        raise DocumentValidationError("Unable to decode text file with supported encodings")

    def _scan_for_suspicious_content(self, content: bytes, declared_type: KnowledgeSourceType) -> None:
        if declared_type not in {KnowledgeSourceType.HTML, KnowledgeSourceType.MD, KnowledgeSourceType.TXT}:
            return
        sample = content[:65536].decode("utf-8", errors="ignore")
        for pattern in _SUSPICIOUS_PATTERNS:
            if pattern.search(sample):
                raise DocumentValidationError("Upload contains potentially unsafe HTML or script content")
