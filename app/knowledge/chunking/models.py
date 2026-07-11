"""Configurable document chunking models."""

from pydantic import Field

from app.core.enums import ChunkStrategyType
from app.core.schemas import SchemaBase


class ChunkConfig(SchemaBase):
    strategy: ChunkStrategyType = Field(default=ChunkStrategyType.RECURSIVE)
    chunk_size: int = Field(default=512, ge=64, le=8192, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=64, ge=0, le=2048)
    separator: str = Field(default="\n\n", max_length=32)
    maximum_tokens: int | None = Field(default=None, ge=32, le=8192)
    preserve_sections: bool = Field(default=True)
    language: str | None = Field(default=None, max_length=16)


class TextChunk(SchemaBase):
    chunk_number: int
    content: str
    char_count: int
    token_count: int | None = None
    metadata: dict | None = None
