"""Knowledge service factory — builds services with isolated sessions."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.knowledge.parser_factory import build_parser_registry
from app.infrastructure.knowledge.registry import get_embedding_provider, get_vector_store
from app.infrastructure.repositories.knowledge_chunk_repository import SqlAlchemyKnowledgeChunkRepository
from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
from app.infrastructure.services.knowledge_ingestion_service import KnowledgeIngestionServiceImpl
from app.knowledge.services.ingestion_service import KnowledgeIngestionService


def build_knowledge_ingestion_service(session: AsyncSession) -> KnowledgeIngestionService:
    return KnowledgeIngestionServiceImpl(
        SqlAlchemyKnowledgeSourceRepository(session),
        SqlAlchemyKnowledgeChunkRepository(session),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
    )
