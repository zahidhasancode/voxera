"""Document validator tests."""

import pytest

from app.core.enums import KnowledgeSourceType
from app.knowledge.validation.document_validator import DocumentValidationError, DocumentValidator


@pytest.fixture
def validator() -> DocumentValidator:
    return DocumentValidator()


def test_valid_txt_upload(validator: DocumentValidator) -> None:
    content = b"Hello knowledge base"
    result = validator.validate_upload(
        filename="notes.txt",
        content=content,
        declared_type=KnowledgeSourceType.TXT,
    )
    assert result.file_hash
    assert result.detected_type == KnowledgeSourceType.TXT


def test_rejects_path_traversal(validator: DocumentValidator) -> None:
    with pytest.raises(DocumentValidationError, match="Path traversal"):
        validator.validate_upload(
            filename="../etc/passwd",
            content=b"secret",
            declared_type=KnowledgeSourceType.TXT,
        )


def test_rejects_extension_mismatch(validator: DocumentValidator) -> None:
    with pytest.raises(DocumentValidationError, match="extension"):
        validator.validate_upload(
            filename="report.pdf",
            content=b"%PDF-1.4 fake",
            declared_type=KnowledgeSourceType.TXT,
        )


def test_rejects_oversized_upload(validator: DocumentValidator, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.knowledge.validation.document_validator.settings.KNOWLEDGE_MAX_UPLOAD_BYTES",
        10,
    )
    with pytest.raises(DocumentValidationError, match="maximum upload size"):
        validator.validate_upload(
            filename="big.txt",
            content=b"x" * 20,
            declared_type=KnowledgeSourceType.TXT,
        )


def test_rejects_script_injection(validator: DocumentValidator) -> None:
    with pytest.raises(DocumentValidationError, match="unsafe"):
        validator.validate_upload(
            filename="page.html",
            content=b"<html><script>alert(1)</script></html>",
            declared_type=KnowledgeSourceType.HTML,
        )
