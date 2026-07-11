"""Integration service factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.integrations.integration_service_impl import IntegrationServiceImpl
from app.infrastructure.repositories.integration.repositories import SqlAlchemyIntegrationRepository
from app.integrations.services.integration_service import IntegrationService


def build_integration_service(session: AsyncSession) -> IntegrationService:
    return IntegrationServiceImpl(SqlAlchemyIntegrationRepository(session))
