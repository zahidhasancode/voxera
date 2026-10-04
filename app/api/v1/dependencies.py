"""FastAPI dependency injection for enterprise domains."""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.service import AgentService
from app.audit.service import AuditLogService
from app.configuration.service import AgentConfigurationService
from app.core.config import settings
from app.database.session import get_db_session
from app.infrastructure.knowledge.persistent_worker import persistent_ingestion_worker
from app.infrastructure.knowledge.providers import get_embedding_provider, get_file_storage, get_vector_store
from app.infrastructure.repositories.agent_repository import SqlAlchemyAgentRepository
from app.infrastructure.repositories.audit_repository import SqlAlchemyAuditLogRepository
from app.infrastructure.repositories.configuration_repository import (
    SqlAlchemyAgentConfigurationRepository,
)
from app.infrastructure.repositories.knowledge_chunk_repository import SqlAlchemyKnowledgeChunkRepository
from app.infrastructure.repositories.knowledge_repository import SqlAlchemyKnowledgeBaseRepository
from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
from app.infrastructure.repositories.tenant_repository import SqlAlchemyTenantRepository
from app.infrastructure.repositories.tool_repository import SqlAlchemyToolRepository
from app.infrastructure.services.agent_service import AgentServiceImpl
from app.infrastructure.services.audit_service import AuditLogServiceImpl
from app.infrastructure.services.configuration_service import AgentConfigurationServiceImpl
from app.infrastructure.services.knowledge_ingestion_service import KnowledgeIngestionServiceImpl
from app.infrastructure.services.knowledge_retrieval_service import RetrievalServiceImpl
from app.infrastructure.services.knowledge_service import KnowledgeBaseServiceImpl
from app.infrastructure.services.knowledge_source_service import KnowledgeSourceServiceImpl
from app.infrastructure.services.tenant_service import TenantServiceImpl
from app.infrastructure.services.tool_service import ToolServiceImpl
from app.infrastructure.memory.factory import build_memory_manager
from app.infrastructure.planner.factory import build_planner_service
from app.infrastructure.verifier.factory import build_verifier_service
from app.infrastructure.workflow.factory import build_workflow_service
from app.infrastructure.iam.factory import build_iam_service
from app.infrastructure.integrations.factory import build_integration_service
from app.infrastructure.rag.factory import build_enterprise_rag_service
from app.infrastructure.tools.factory import build_tool_registry
from app.core.exception_handlers import resolve_exception
from app.knowledge.services.ingestion_service import KnowledgeIngestionService
from app.knowledge.services.knowledge_base_service import KnowledgeBaseService
from app.knowledge.services.retrieval_service import RetrievalService
from app.knowledge.services.source_service import KnowledgeSourceService
from app.tenants.service import TenantService
from app.tools.service import ToolService


def _require_database() -> None:
    if not settings.database_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured. Set DATABASE_URL to enable enterprise APIs.",
        )


async def get_session(
    _: None = Depends(_require_database),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_tenant_service(session: AsyncSession = Depends(get_session)) -> TenantService:
    return TenantServiceImpl(SqlAlchemyTenantRepository(session))


def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    return AgentServiceImpl(SqlAlchemyAgentRepository(session))


def get_agent_configuration_service(
    session: AsyncSession = Depends(get_session),
) -> AgentConfigurationService:
    return AgentConfigurationServiceImpl(SqlAlchemyAgentConfigurationRepository(session))


def get_knowledge_base_service(
    session: AsyncSession = Depends(get_session),
) -> KnowledgeBaseService:
    return KnowledgeBaseServiceImpl(SqlAlchemyKnowledgeBaseRepository(session))


def get_knowledge_ingestion_service(
    session: AsyncSession = Depends(get_session),
) -> KnowledgeIngestionService:
    return KnowledgeIngestionServiceImpl(
        SqlAlchemyKnowledgeSourceRepository(session),
        SqlAlchemyKnowledgeChunkRepository(session),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
        background_processor=persistent_ingestion_worker,
    )


def get_background_ingestion_processor():
    return persistent_ingestion_worker


def get_knowledge_source_service(
    session: AsyncSession = Depends(get_session),
    background_processor=Depends(get_background_ingestion_processor),
) -> KnowledgeSourceService:
    return KnowledgeSourceServiceImpl(
        SqlAlchemyKnowledgeSourceRepository(session),
        get_file_storage(),
        background_processor,
        vector_store=get_vector_store(),
    )


def get_retrieval_service(
    session: AsyncSession = Depends(get_session),
) -> RetrievalService:
    return RetrievalServiceImpl(
        SqlAlchemyKnowledgeSourceRepository(session),
        SqlAlchemyKnowledgeChunkRepository(session),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )


def get_enterprise_rag_service(session: AsyncSession = Depends(get_session)):
    return build_enterprise_rag_service(session)


def get_memory_manager(session: AsyncSession = Depends(get_session)):
    return build_memory_manager(session)


def get_tool_service(session: AsyncSession = Depends(get_session)) -> ToolService:
    return ToolServiceImpl(SqlAlchemyToolRepository(session))


def get_tool_registry(session: AsyncSession = Depends(get_session)):
    return build_tool_registry(session)


def get_planner_service(session: AsyncSession = Depends(get_session)):
    return build_planner_service(session)


def get_verifier_service(session: AsyncSession = Depends(get_session)):
    return build_verifier_service(session)


def get_workflow_service(session: AsyncSession = Depends(get_session)):
    return build_workflow_service(session)


def get_iam_service(session: AsyncSession = Depends(get_session)):
    return build_iam_service(session)


def get_audit_log_service(session: AsyncSession = Depends(get_session)) -> AuditLogService:
    return AuditLogServiceImpl(SqlAlchemyAuditLogRepository(session))


def get_integration_service(session: AsyncSession = Depends(get_session)):
    return build_integration_service(session)


def map_domain_errors(exc: Exception) -> HTTPException:
    """Map domain exceptions to HTTPException with standard error envelope."""
    status_code, body = resolve_exception(exc)
    return HTTPException(status_code=status_code, detail=body)
