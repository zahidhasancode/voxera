"""Unit tests for RetrievalValidator."""

import pytest
from uuid import uuid4

from app.core.enums import AgentStatus, KnowledgeSourceStatus
from app.core.exceptions import CrossTenantAccessError, RetrievalValidationError
from app.rag.interfaces.models import NormalizedQuery, RankedChunk, RetrievalRequest, RetrievalResponse
from app.rag.validators.retrieval_validator import RetrievalValidator


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def validator():
    return RetrievalValidator()


def _response(tenant_id, chunks, agent_id=None):
    return RetrievalResponse(
        tenant_id=tenant_id,
        agent_id=agent_id,
        query=NormalizedQuery(original="q", normalized="q", language="en"),
        chunks=chunks,
        total_candidates=len(chunks),
        average_similarity=0.9,
        retrieval_latency_ms=10,
        embedding_latency_ms=5,
        ranking_latency_ms=1,
    )


def test_validator_rejects_cross_tenant_chunk(validator, tenant_id):
    other_tenant = uuid4()
    chunk = RankedChunk(
        chunk_id=uuid4(),
        source_id=uuid4(),
        tenant_id=other_tenant,
        content="secret",
        score=0.95,
        rank=0,
    )
    request = RetrievalRequest(tenant_id=tenant_id, query="test")
    response = _response(tenant_id, [chunk])

    with pytest.raises(CrossTenantAccessError):
        validator.validate_retrieval(request, response)


def test_validator_rejects_low_similarity(validator, tenant_id):
    chunk = RankedChunk(
        chunk_id=uuid4(),
        source_id=uuid4(),
        tenant_id=tenant_id,
        content="content",
        score=0.1,
        rank=0,
    )
    request = RetrievalRequest(tenant_id=tenant_id, query="test", min_similarity=0.8)
    response = _response(tenant_id, [chunk])

    with pytest.raises(RetrievalValidationError) as exc_info:
        validator.validate_retrieval(request, response)
    assert any("below_similarity_threshold" in v for v in exc_info.value.violations)


def test_validator_rejects_duplicate_chunks(validator, tenant_id):
    chunk_id = uuid4()
    chunks = [
        RankedChunk(
            chunk_id=chunk_id,
            source_id=uuid4(),
            tenant_id=tenant_id,
            content="same",
            score=0.9,
            rank=0,
        ),
        RankedChunk(
            chunk_id=chunk_id,
            source_id=uuid4(),
            tenant_id=tenant_id,
            content="same",
            score=0.85,
            rank=1,
        ),
    ]
    request = RetrievalRequest(tenant_id=tenant_id, query="test", min_similarity=0.0)
    response = _response(tenant_id, chunks)

    with pytest.raises(RetrievalValidationError) as exc_info:
        validator.validate_retrieval(request, response)
    assert any("duplicate_chunk" in v for v in exc_info.value.violations)


def test_validator_rejects_inactive_source(validator, tenant_id):
    source_id = uuid4()
    chunk = RankedChunk(
        chunk_id=uuid4(),
        source_id=source_id,
        tenant_id=tenant_id,
        content="content",
        score=0.95,
        rank=0,
    )
    request = RetrievalRequest(tenant_id=tenant_id, query="test", min_similarity=0.0)
    response = _response(tenant_id, [chunk])

    with pytest.raises(RetrievalValidationError):
        validator.validate_retrieval(
            request,
            response,
            source_statuses={source_id: KnowledgeSourceStatus.PROCESSING},
        )


def test_validator_passes_valid_retrieval(validator, tenant_id):
    source_id = uuid4()
    chunk = RankedChunk(
        chunk_id=uuid4(),
        source_id=source_id,
        tenant_id=tenant_id,
        content="Valid enterprise content.",
        score=0.92,
        rank=0,
        language="en",
    )
    request = RetrievalRequest(
        tenant_id=tenant_id,
        query="test",
        min_similarity=0.5,
        agent_id=uuid4(),
    )
    response = _response(tenant_id, [chunk], agent_id=request.agent_id)

    validator.validate_retrieval(
        request,
        response,
        agent_status=AgentStatus.ACTIVE,
        agent_tenant_id=tenant_id,
        agent_language="en",
        source_statuses={source_id: KnowledgeSourceStatus.READY},
    )
