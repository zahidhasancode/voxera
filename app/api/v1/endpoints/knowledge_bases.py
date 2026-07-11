"""Knowledge base REST endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_knowledge_base_service, map_domain_errors
from app.core.schemas import PaginatedResponse
from app.knowledge.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.knowledge.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter()


class KnowledgeBaseListResponse(PaginatedResponse):
    items: list[KnowledgeBaseRead]


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    tenant_id: UUID,
    body: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseRead:
    payload = body.model_copy(update={"tenant_id": tenant_id})
    return await service.create_knowledge_base(payload)


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseListResponse:
    items, total = await service.list_knowledge_bases(tenant_id, offset=offset, limit=limit)
    return KnowledgeBaseListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
async def get_knowledge_base(
    tenant_id: UUID,
    knowledge_base_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseRead:
    try:
        return await service.get_knowledge_base(tenant_id, knowledge_base_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
async def update_knowledge_base(
    tenant_id: UUID,
    knowledge_base_id: UUID,
    body: KnowledgeBaseUpdate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseRead:
    try:
        return await service.update_knowledge_base(tenant_id, knowledge_base_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    tenant_id: UUID,
    knowledge_base_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> None:
    try:
        await service.delete_knowledge_base(tenant_id, knowledge_base_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
