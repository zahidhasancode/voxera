"""RAG subsystem factory and singletons."""

from functools import lru_cache

from app.infrastructure.knowledge.providers import get_embedding_provider, get_vector_store
from app.infrastructure.rag.agent_scope import SqlAlchemyAgentKnowledgeScope
from app.rag.cache.base import InMemoryRetrievalCache, RetrievalCache
from app.rag.context.builder import ContextBuilder
from app.rag.prompt_builder.enterprise import EnterprisePromptBuilder
from app.rag.ranking.strategies import CosineSimilarityRankingStrategy, RankingStrategyRegistry
from app.rag.retriever.enterprise_retriever import EnterpriseRetrieverImpl
from app.rag.validators.retrieval_validator import RetrievalValidator


@lru_cache
def get_retrieval_cache() -> RetrievalCache:
    return InMemoryRetrievalCache()


@lru_cache
def get_ranking_registry() -> RankingStrategyRegistry:
    registry = RankingStrategyRegistry()
    registry.register(CosineSimilarityRankingStrategy())
    return registry


def build_enterprise_retriever(session) -> EnterpriseRetrieverImpl:
    from app.infrastructure.repositories.agent_repository import SqlAlchemyAgentRepository
    from app.infrastructure.repositories.knowledge_chunk_repository import SqlAlchemyKnowledgeChunkRepository
    from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository

    return EnterpriseRetrieverImpl(
        source_repository=SqlAlchemyKnowledgeSourceRepository(session),
        chunk_repository=SqlAlchemyKnowledgeChunkRepository(session),
        embedding_provider=get_embedding_provider(),
        vector_store=get_vector_store(),
        agent_scope=SqlAlchemyAgentKnowledgeScope(SqlAlchemyAgentRepository(session)),
        ranking_registry=get_ranking_registry(),
        cache=get_retrieval_cache(),
    )


def build_enterprise_rag_service(session) -> "EnterpriseRAGService":
    from app.infrastructure.repositories.agent_repository import SqlAlchemyAgentRepository
    from app.infrastructure.repositories.knowledge_source_repository import SqlAlchemyKnowledgeSourceRepository
    from app.infrastructure.repositories.tenant_repository import SqlAlchemyTenantRepository
    from app.rag.services.enterprise_rag_service import EnterpriseRAGService

    return EnterpriseRAGService(
        retriever=build_enterprise_retriever(session),
        context_builder=ContextBuilder(),
        prompt_builder=EnterprisePromptBuilder(),
        validator=RetrievalValidator(),
        agent_repository=SqlAlchemyAgentRepository(session),
        source_repository=SqlAlchemyKnowledgeSourceRepository(session),
        tenant_repository=SqlAlchemyTenantRepository(session),
    )
