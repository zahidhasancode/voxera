"""Parser registry tests."""

import asyncio
from pathlib import Path

import pytest

from app.core.enums import KnowledgeSourceType
from app.infrastructure.knowledge.parser_factory import build_parser_registry


@pytest.fixture
def registry():
    return build_parser_registry()


def test_registry_resolves_supported_types(registry) -> None:
    for source_type in (
        KnowledgeSourceType.TXT,
        KnowledgeSourceType.MD,
        KnowledgeSourceType.PDF,
        KnowledgeSourceType.DOCX,
        KnowledgeSourceType.CSV_FAQ,
        KnowledgeSourceType.HTML,
        KnowledgeSourceType.WEBSITE,
    ):
        parser = registry.resolve(source_type)
        assert parser.supports(source_type)


def test_plain_text_parser(tmp_path: Path, registry) -> None:
    path = tmp_path / "sample.md"
    path.write_text("# Hello\n\nWorld", encoding="utf-8")
    parser = registry.resolve(KnowledgeSourceType.MD)
    doc = asyncio.run(parser.parse_file(str(path), source_type=KnowledgeSourceType.MD))
    assert "Hello" in doc.text
    assert doc.pages


def test_csv_parser(tmp_path: Path, registry) -> None:
    path = tmp_path / "faq.csv"
    path.write_text("question,answer\nWhat is VOXERA?,Voice platform\n", encoding="utf-8")
    parser = registry.resolve(KnowledgeSourceType.CSV_FAQ)
    doc = asyncio.run(parser.parse_file(str(path), source_type=KnowledgeSourceType.CSV_FAQ))
    assert "VOXERA" in doc.text


def test_unsupported_integrations_raise(registry) -> None:
    parser = registry.resolve(KnowledgeSourceType.NOTION)
    with pytest.raises(Exception):
        asyncio.run(parser.parse_file("unused", source_type=KnowledgeSourceType.NOTION))
