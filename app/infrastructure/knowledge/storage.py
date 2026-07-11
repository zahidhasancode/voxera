"""File storage abstraction for knowledge uploads."""

from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.core.config import settings


class KnowledgeFileStorage(ABC):
    @abstractmethod
    async def save(
        self,
        tenant_id: UUID,
        source_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        """Persist file and return storage path."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, file_path: str) -> None:
        raise NotImplementedError


class LocalKnowledgeFileStorage(KnowledgeFileStorage):
    """Filesystem-backed storage with tenant/source isolation."""

    def __init__(self, base_path: str | None = None) -> None:
        self._base = Path(base_path or settings.KNOWLEDGE_STORAGE_PATH)

    async def save(
        self,
        tenant_id: UUID,
        source_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        safe_name = Path(filename).name
        directory = self._base / str(tenant_id) / str(source_id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / safe_name
        target.write_bytes(content)
        return str(target.resolve())

    async def delete(self, file_path: str) -> None:
        path = Path(file_path)
        if path.is_file():
            path.unlink()
        parent = path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
