"""Enterprise RAG orchestration service."""

from uuid import UUID

from app.core.config import settings
from app.core.enums import AgentStatus, KnowledgeSourceStatus
from app.core.exceptions import NotFoundError
from app.rag.context.builder import ContextBuilder
from app.rag.interfaces.models import EnterpriseRAGResult, RetrievalRequest
from app.rag.interfaces.retriever import EnterpriseRetriever
from app.rag.metrics.collector import RetrievalMetricsCollector
from app.rag.prompt_builder.enterprise import EnterprisePromptBuilder
from app.rag.validators.retrieval_validator import RetrievalValidator


class EnterpriseRAGService:
    """
    Full retrieval pipeline orchestrator.

    Pipeline:
    Language Detection → Query Normalization → Embedding → Vector Search
    → Metadata Filtering → Ranking → Context Compression → Validation → Prompt Builder
    """

    def __init__(
        self,
        *,
        retriever: EnterpriseRetriever,
        context_builder: ContextBuilder,
        prompt_builder: EnterprisePromptBuilder,
        validator: RetrievalValidator,
        agent_repository=None,
        source_repository=None,
        tenant_repository=None,
    ) -> None:
        self._retriever = retriever
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._validator = validator
        self._agents = agent_repository
        self._sources = source_repository
        self._tenants = tenant_repository

    async def execute(self, request: RetrievalRequest) -> EnterpriseRAGResult:
        metrics = RetrievalMetricsCollector(
            tenant_id=str(request.tenant_id),
            agent_id=str(request.agent_id) if request.agent_id else None,
        )

        async with metrics.measure("retrieval"):
            retrieval = await self._retriever.retrieve(request)

        agent_status = None
        agent_tenant_id = None
        agent_language = None
        agent_system_prompt = None
        tenant_name = "Company"
        available_tools: list[str] = []

        if request.agent_id and self._agents:
            agent = await self._agents.get_by_id(request.tenant_id, request.agent_id)
            if agent is None:
                raise NotFoundError(f"Agent {request.agent_id} not found")
            agent_status = AgentStatus(agent.status)
            agent_tenant_id = agent.tenant_id
            agent_language = agent.language
            agent_system_prompt = agent.system_prompt

        source_statuses = await self._load_source_statuses(request, retrieval)

        self._validator.validate_retrieval(
            request,
            retrieval,
            agent_status=agent_status,
            agent_tenant_id=agent_tenant_id,
            agent_language=agent_language,
            source_statuses=source_statuses,
        )

        metrics.record_chunks(len(retrieval.chunks), retrieval.average_similarity)

        async with metrics.measure("context_build"):
            context = await self._context_builder.build(
                retrieval.chunks,
                tenant_id=request.tenant_id,
                agent_id=request.agent_id,
            )

        self._validator.validate_context(request, context)
        metrics.record_tokens(context_tokens=context.token_estimate, prompt_tokens=0)

        prompt = None
        if request.include_prompt:
            if self._tenants:
                tenant = await self._tenants.get_by_id(request.tenant_id)
                if tenant:
                    tenant_name = tenant.company_name

            async with metrics.measure("prompt_build"):
                prompt = await self._prompt_builder.build(
                    tenant_name=tenant_name,
                    agent_system_prompt=agent_system_prompt or "You are a helpful voice agent.",
                    agent_language=agent_language or retrieval.query.language or "en",
                    built_context=context,
                    user_query=request.query,
                    conversation=request.conversation,
                    available_tools=available_tools,
                )
            metrics.record_tokens(
                context_tokens=context.token_estimate,
                prompt_tokens=prompt.token_estimate,
            )

        retrieval = retrieval.model_copy(update={"validated": True})
        metrics.emit_summary()

        return EnterpriseRAGResult(
            retrieval=retrieval,
            context=context,
            prompt=prompt,
            metrics=metrics.snapshot(),
        )

    async def _load_source_statuses(self, request, retrieval) -> dict[UUID, KnowledgeSourceStatus]:
        if not self._sources or not retrieval.chunks:
            return {}
        source_ids = list({c.source_id for c in retrieval.chunks})
        sources = await self._sources.list_by_ids(request.tenant_id, source_ids)
        return {s.id: KnowledgeSourceStatus(s.status) for s in sources}
