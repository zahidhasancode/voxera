"""SQLAlchemy audit log repository."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.audit.schemas import AuditLogCreate, AuditLogFilter, AuditLogRead
from app.database.models.audit import AuditLogModel
from app.infrastructure.repositories._helpers import enum_values


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, data: AuditLogCreate) -> AuditLogRead:
        payload = enum_values(data)
        metadata = payload.pop("metadata", None)
        resource_id = payload.pop("resource_id", None)
        row = AuditLogModel(
            **payload,
            metadata_=metadata,
            resource_id=str(resource_id) if resource_id else None,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return AuditLogRead.model_validate(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        filters: AuditLogFilter | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLogRead], int]:
        query = select(AuditLogModel).where(AuditLogModel.tenant_id == tenant_id)
        if filters:
            if filters.action:
                query = query.where(AuditLogModel.action == filters.action)
            if filters.actor_type:
                query = query.where(AuditLogModel.actor_type == filters.actor_type.value)
            if filters.resource_type:
                query = query.where(AuditLogModel.resource_type == filters.resource_type)
            if filters.resource_id:
                query = query.where(AuditLogModel.resource_id == str(filters.resource_id))
            if filters.since:
                query = query.where(AuditLogModel.created_at >= filters.since)
            if filters.until:
                query = query.where(AuditLogModel.created_at <= filters.until)

        total = await self._session.scalar(
            select(func.count()).select_from(query.subquery())
        )
        result = await self._session.execute(
            query.order_by(AuditLogModel.created_at.desc()).offset(offset).limit(limit)
        )
        rows = result.scalars().all()
        return [AuditLogRead.model_validate(r) for r in rows], int(total or 0)

    async def get_by_id(
        self,
        tenant_id: UUID,
        audit_log_id: UUID,
    ) -> AuditLogRead | None:
        result = await self._session.execute(
            select(AuditLogModel).where(
                AuditLogModel.tenant_id == tenant_id,
                AuditLogModel.id == audit_log_id,
            )
        )
        row = result.scalar_one_or_none()
        return AuditLogRead.model_validate(row) if row else None
