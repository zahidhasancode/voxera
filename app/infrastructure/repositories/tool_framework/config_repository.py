"""SQLAlchemy tenant tool config repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tool_framework import TenantToolConfigModel
from app.tools.repository.execution import TenantToolConfigRepository
from app.tools.schemas.execution import TenantToolConfigRead


class SqlAlchemyTenantToolConfigRepository(TenantToolConfigRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, tenant_id: UUID, tool_slug: str) -> TenantToolConfigRead | None:
        result = await self._session.execute(
            select(TenantToolConfigModel).where(
                TenantToolConfigModel.tenant_id == tenant_id,
                TenantToolConfigModel.tool_slug == tool_slug,
            )
        )
        row = result.scalar_one_or_none()
        return TenantToolConfigRead.model_validate(row) if row else None

    async def list_for_tenant(self, tenant_id: UUID) -> list[TenantToolConfigRead]:
        result = await self._session.execute(
            select(TenantToolConfigModel).where(TenantToolConfigModel.tenant_id == tenant_id)
        )
        return [TenantToolConfigRead.model_validate(r) for r in result.scalars().all()]

    async def upsert(self, config: TenantToolConfigRead) -> TenantToolConfigRead:
        result = await self._session.execute(
            select(TenantToolConfigModel).where(
                TenantToolConfigModel.tenant_id == config.tenant_id,
                TenantToolConfigModel.tool_slug == config.tool_slug,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = TenantToolConfigModel(
                id=config.id,
                tenant_id=config.tenant_id,
                tool_slug=config.tool_slug,
                enabled=config.enabled,
                credentials_ref=config.credentials_ref,
                provider_config=config.provider_config,
                rate_limit_per_minute=config.rate_limit_per_minute,
                timeout_seconds=config.timeout_seconds,
                metadata_=None,
            )
            self._session.add(row)
        else:
            row.enabled = config.enabled
            row.credentials_ref = config.credentials_ref
            row.provider_config = config.provider_config
            row.rate_limit_per_minute = config.rate_limit_per_minute
            row.timeout_seconds = config.timeout_seconds
        await self._session.flush()
        await self._session.refresh(row)
        return TenantToolConfigRead.model_validate(row)
