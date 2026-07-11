"""Enterprise RAG REST API — thin delegation layer."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_enterprise_rag_service, map_domain_errors
from app.core.exceptions import RetrievalValidationError
from app.rag.interfaces.models import EnterpriseRAGResult, RetrievalRequest

router = APIRouter()


@router.post("/query", response_model=EnterpriseRAGResult, status_code=status.HTTP_200_OK)
async def rag_query(
    tenant_id: UUID,
    agent_id: UUID,
    body: RetrievalRequest,
    service=Depends(get_enterprise_rag_service),
) -> EnterpriseRAGResult:
    payload = body.model_copy(update={"tenant_id": tenant_id, "agent_id": agent_id})
    try:
        return await service.execute(payload)
    except RetrievalValidationError as exc:
        raise map_domain_errors(exc) from exc
    except Exception as exc:
        raise map_domain_errors(exc) from exc
