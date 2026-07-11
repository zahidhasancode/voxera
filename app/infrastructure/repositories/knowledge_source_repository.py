"""SQLAlchemy knowledge source repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    KnowledgeEmbeddingStatus,
    KnowledgeProcessingStage,
    KnowledgeSourceStatus,
)
from app.database.models.knowledge_source import KnowledgeSourceModel
from app.infrastructure.repositories._helpers import apply_partial_update, enum_values
from app.knowledge.repository.source_repository import KnowledgeSourceRepository
from app.knowledge.retrieval.vector_store import VectorStore
from app.knowledge.schemas.source import (
    KnowledgeSourceCreate,
    KnowledgeSourceRead,
    KnowledgeSourceStatusSummary,
    KnowledgeSourceUpdate,
)


class SqlAlchemyKnowledgeSourceRepository(KnowledgeSourceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: KnowledgeSourceCreate) -> KnowledgeSourceRead:
        payload = enum_values(data)
        metadata = payload.pop("metadata", None)
        chunk_config = payload.pop("chunk_config", None)
        row = KnowledgeSourceModel(
            **payload,
            vector_namespace="pending",
            metadata_=metadata,
            chunk_config=chunk_config,
        )
        self._session.add(row)
        await self._session.flush()
        row.vector_namespace = VectorStore.build_tenant_namespace(row.tenant_id, row.id)
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeSourceRead.model_validate(row)

    async def get_by_id(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceRead | None:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.tenant_id == tenant_id,
                KnowledgeSourceModel.id == source_id,
            )
        )
        row = result.scalar_one_or_none()
        return KnowledgeSourceRead.model_validate(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        status: KnowledgeSourceStatus | None = None,
    ) -> tuple[list[KnowledgeSourceRead], int]:
        query = select(KnowledgeSourceModel).where(KnowledgeSourceModel.tenant_id == tenant_id)
        if status is not None:
            query = query.where(KnowledgeSourceModel.status == status.value)
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        result = await self._session.execute(
            query.order_by(KnowledgeSourceModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [KnowledgeSourceRead.model_validate(r) for r in rows], int(total or 0)

    async def update(
        self,
        tenant_id: UUID,
        source_id: UUID,
        data: KnowledgeSourceUpdate,
    ) -> KnowledgeSourceRead | None:
        row = await self._get_row(tenant_id, source_id)
        if row is None:
            return None
        apply_partial_update(row, data)
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeSourceRead.model_validate(row)

    async def update_file_info(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        file_path: str,
        file_size_bytes: int,
        content_type: str | None,
        original_filename: str | None,
        file_hash: str | None = None,
    ) -> KnowledgeSourceRead | None:
        row = await self._get_row(tenant_id, source_id)
        if row is None:
            return None
        row.file_path = file_path
        row.file_size_bytes = file_size_bytes
        row.content_type = content_type
        row.original_filename = original_filename
        if file_hash is not None:
            row.file_hash = file_hash
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeSourceRead.model_validate(row)

    async def find_by_file_hash(self, tenant_id: UUID, file_hash: str) -> KnowledgeSourceRead | None:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.tenant_id == tenant_id,
                KnowledgeSourceModel.file_hash == file_hash,
            )
        )
        row = result.scalar_one_or_none()
        return KnowledgeSourceRead.model_validate(row) if row else None

    async def update_processing_state(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        status: KnowledgeSourceStatus | None = None,
        stage: KnowledgeProcessingStage | None = None,
        progress_pct: int | None = None,
        processing_started_at: datetime | None = None,
        processing_completed_at: datetime | None = None,
        processing_error: str | None = None,
        chunk_count: int | None = None,
        embedding_count: int | None = None,
        embedding_status: KnowledgeEmbeddingStatus | None = None,
    ) -> KnowledgeSourceRead | None:
        row = await self._get_row(tenant_id, source_id)
        if row is None:
            return None
        if status is not None:
            row.status = status.value
        if stage is not None:
            row.processing_stage = stage.value
        if progress_pct is not None:
            row.progress_pct = progress_pct
        if processing_started_at is not None:
            row.processing_started_at = processing_started_at
        if processing_completed_at is not None:
            row.processing_completed_at = processing_completed_at
        if processing_error is not None:
            row.processing_error = processing_error
        if chunk_count is not None:
            row.chunk_count = chunk_count
        if embedding_count is not None:
            row.embedding_count = embedding_count
        if embedding_status is not None:
            row.embedding_status = embedding_status.value
        await self._session.flush()
        await self._session.refresh(row)
        return KnowledgeSourceRead.model_validate(row)

    async def delete(self, tenant_id: UUID, source_id: UUID) -> bool:
        row = await self._get_row(tenant_id, source_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def get_status_summary(self, tenant_id: UUID) -> KnowledgeSourceStatusSummary:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(KnowledgeSourceModel.tenant_id == tenant_id)
        )
        rows = result.scalars().all()
        summary = KnowledgeSourceStatusSummary(
            tenant_id=tenant_id,
            total_sources=len(rows),
            pending=0,
            processing=0,
            ready=0,
            failed=0,
            total_chunks=0,
            total_embeddings=0,
        )
        for row in rows:
            summary.total_chunks += row.chunk_count
            summary.total_embeddings += row.embedding_count
            if row.status == KnowledgeSourceStatus.PENDING:
                summary.pending += 1
            elif row.status in (
                KnowledgeSourceStatus.PROCESSING,
                KnowledgeSourceStatus.REPROCESSING,
            ):
                summary.processing += 1
            elif row.status == KnowledgeSourceStatus.READY:
                summary.ready += 1
            elif row.status == KnowledgeSourceStatus.FAILED:
                summary.failed += 1
        return summary

    async def list_by_ids(
        self,
        tenant_id: UUID,
        source_ids: list[UUID],
    ) -> list[KnowledgeSourceRead]:
        if not source_ids:
            return []
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.tenant_id == tenant_id,
                KnowledgeSourceModel.id.in_(source_ids),
            )
        )
        return [KnowledgeSourceRead.model_validate(r) for r in result.scalars().all()]

    async def _get_row(self, tenant_id: UUID, source_id: UUID) -> KnowledgeSourceModel | None:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.tenant_id == tenant_id,
                KnowledgeSourceModel.id == source_id,
            )
        )
        return result.scalar_one_or_none()
