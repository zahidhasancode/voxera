"""Knowledge ingestion REST API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.api.v1.dependencies import (
    get_background_ingestion_processor,
    get_knowledge_source_service,
    map_domain_errors,
)
from app.knowledge.schemas.ingestion import IngestionJobStatus
from app.core.schemas import PaginatedResponse
from app.knowledge.schemas.source import (
    KnowledgeReprocessRequest,
    KnowledgeSourceCreate,
    KnowledgeSourceFrontendRead,
    KnowledgeSourceStatusSummary,
)
from app.knowledge.services.source_service import KnowledgeSourceService

router = APIRouter()


class KnowledgeSourceListResponse(PaginatedResponse):
    items: list[KnowledgeSourceFrontendRead]


@router.get("/jobs/{job_id}", response_model=IngestionJobStatus)
async def get_ingestion_job(
    tenant_id: UUID,
    job_id: str,
    processor=Depends(get_background_ingestion_processor),
) -> IngestionJobStatus:
    status_row = await processor.get_status(job_id)
    if status_row is None or status_row.tenant_id != tenant_id:
        from app.core.exceptions import NotFoundError

        raise map_domain_errors(NotFoundError(f"Ingestion job {job_id} not found")) from None
    return status_row


@router.post("/upload", response_model=KnowledgeSourceFrontendRead, status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    tenant_id: UUID,
    title: str = Form(...),
    source_type: str = Form(...),
    file: UploadFile = File(...),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> KnowledgeSourceFrontendRead:
    content = await file.read()
    try:
        return await service.upload_file(
            tenant_id,
            title=title,
            source_type=source_type,
            file_content=content,
            filename=file.filename or "upload",
            content_type=file.content_type,
        )
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("", response_model=KnowledgeSourceFrontendRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_from_url(
    tenant_id: UUID,
    body: KnowledgeSourceCreate,
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> KnowledgeSourceFrontendRead:
    payload = body.model_copy(update={"tenant_id": tenant_id})
    return await service.create_from_url(tenant_id, payload)


@router.get("", response_model=KnowledgeSourceListResponse)
async def list_knowledge(
    tenant_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> KnowledgeSourceListResponse:
    items, total = await service.list_sources(tenant_id, offset=offset, limit=limit)
    return KnowledgeSourceListResponse(total=total, offset=offset, limit=limit, items=items)


@router.get("/status", response_model=KnowledgeSourceStatusSummary)
async def get_knowledge_status(
    tenant_id: UUID,
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> KnowledgeSourceStatusSummary:
    return await service.get_status_summary(tenant_id)


@router.get("/{source_id}", response_model=KnowledgeSourceFrontendRead)
async def get_knowledge(
    tenant_id: UUID,
    source_id: UUID,
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> KnowledgeSourceFrontendRead:
    try:
        return await service.get_source(tenant_id, source_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    tenant_id: UUID,
    source_id: UUID,
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> None:
    try:
        await service.delete_source(tenant_id, source_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/reprocess", response_model=list[KnowledgeSourceFrontendRead])
async def reprocess_knowledge(
    tenant_id: UUID,
    body: KnowledgeReprocessRequest,
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
) -> list[KnowledgeSourceFrontendRead]:
    return await service.reprocess(tenant_id, body)
