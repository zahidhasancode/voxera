"""SQLAlchemy knowledge chunk repository."""

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.knowledge_source import KnowledgeChunkModel
from app.knowledge.repository.chunk_repository import KnowledgeChunkRepository
from app.knowledge.schemas.chunk import ChunkMetadata, KnowledgeChunkCreate, KnowledgeChunkRead


class SqlAlchemyKnowledgeChunkRepository(KnowledgeChunkRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(self, chunks: list[KnowledgeChunkCreate]) -> list[KnowledgeChunkRead]:
        rows: list[KnowledgeChunkModel] = []
        for data in chunks:
            payload = data.model_dump(mode="json")
            meta = payload.pop("chunk_metadata", None)
            row = KnowledgeChunkModel(**payload, chunk_metadata=meta)
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        for row in rows:
            await self._session.refresh(row)
        return [self._to_read(r) for r in rows]

    async def list_by_source(
        self,
        tenant_id: UUID,
        source_id: UUID,
        *,
        offset: int = 0,
        limit: int = 500,
    ) -> tuple[list[KnowledgeChunkRead], int]:
        query = select(KnowledgeChunkModel).where(
            KnowledgeChunkModel.tenant_id == tenant_id,
            KnowledgeChunkModel.source_id == source_id,
        )
        total = await self._session.scalar(select(func.count()).select_from(query.subquery()))
        result = await self._session.execute(
            query.order_by(KnowledgeChunkModel.chunk_number).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [self._to_read(r) for r in rows], int(total or 0)

    async def delete_by_source(self, tenant_id: UUID, source_id: UUID) -> int:
        result = await self._session.execute(
            delete(KnowledgeChunkModel).where(
                KnowledgeChunkModel.tenant_id == tenant_id,
                KnowledgeChunkModel.source_id == source_id,
            )
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def update_vector_ids(
        self,
        tenant_id: UUID,
        chunk_vector_map: dict[str, str],
    ) -> None:
        for chunk_id, vector_id in chunk_vector_map.items():
            await self._session.execute(
                update(KnowledgeChunkModel)
                .where(
                    KnowledgeChunkModel.tenant_id == tenant_id,
                    KnowledgeChunkModel.id == chunk_id,
                )
                .values(vector_id=vector_id)
            )
        await self._session.flush()

    async def get_by_ids(
        self,
        tenant_id: UUID,
        chunk_ids: list[UUID],
    ) -> list[KnowledgeChunkRead]:
        if not chunk_ids:
            return []
        result = await self._session.execute(
            select(KnowledgeChunkModel).where(
                KnowledgeChunkModel.tenant_id == tenant_id,
                KnowledgeChunkModel.id.in_(chunk_ids),
            )
        )
        return [self._to_read(r) for r in result.scalars().all()]

    @staticmethod
    def _to_read(row: KnowledgeChunkModel) -> KnowledgeChunkRead:
        meta = ChunkMetadata.model_validate(row.chunk_metadata) if row.chunk_metadata else None
        return KnowledgeChunkRead(
            id=row.id,
            tenant_id=row.tenant_id,
            source_id=row.source_id,
            chunk_number=row.chunk_number,
            content=row.content,
            token_count=row.token_count,
            char_count=row.char_count,
            vector_id=row.vector_id,
            chunk_metadata=meta,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
