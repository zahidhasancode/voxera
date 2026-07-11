"""Memory subsystem factory."""

from functools import lru_cache

from app.infrastructure.memory.memory_manager import MemoryManagerImpl
from app.infrastructure.repositories.memory.conversation_repository import SqlAlchemyConversationRepository
from app.infrastructure.repositories.memory.summary_repository import SqlAlchemyConversationSummaryRepository
from app.infrastructure.repositories.memory.tool_execution_repository import SqlAlchemyToolExecutionRepository
from app.infrastructure.repositories.memory.turn_repository import SqlAlchemyConversationTurnRepository
from app.infrastructure.repositories.memory.working_memory_repository import SqlAlchemyWorkingMemoryRepository
from app.infrastructure.memory.knowledge_memory import CachedKnowledgeMemory
from app.memory.cache.base import InMemoryMemoryCache, MemoryCache
from app.memory.compression.compressor import MemoryCompressor
from app.memory.manager.memory_manager import MemoryManager
from app.memory.state.context_assembler import PlannerContextAssembler
from app.memory.summarizer.conversation_summarizer import StructuredConversationSummarizer
from app.memory.validators.access_validator import MemoryAccessValidator


@lru_cache
def get_memory_cache() -> MemoryCache:
    return InMemoryMemoryCache()


def build_memory_manager(session) -> MemoryManager:
    cache = get_memory_cache()
    return MemoryManagerImpl(
        conversations=SqlAlchemyConversationRepository(session),
        turns=SqlAlchemyConversationTurnRepository(session),
        working_memory=SqlAlchemyWorkingMemoryRepository(session),
        tool_executions=SqlAlchemyToolExecutionRepository(session),
        summaries=SqlAlchemyConversationSummaryRepository(session),
        summarizer=StructuredConversationSummarizer(),
        compressor=MemoryCompressor(),
        validator=MemoryAccessValidator(),
        context_assembler=PlannerContextAssembler(),
        knowledge_memory=CachedKnowledgeMemory(cache),
        cache=cache,
    )
