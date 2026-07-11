"""Verifier REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_verifier_service, map_domain_errors
from app.verifier.schemas import VerifyRequest, VerifierHistoryRead, VerifierMetricsSnapshot, VerifierResult
from app.verifier.services.verifier_service import VerifierService

router = APIRouter()


@router.post("/verify", response_model=VerifierResult)
async def verify_plan(
    tenant_id: UUID,
    agent_id: UUID,
    body: VerifyRequest,
    service: VerifierService = Depends(get_verifier_service),
) -> VerifierResult:
    try:
        return await service.verify(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/history", response_model=list[VerifierHistoryRead])
async def get_verifier_history(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    service: VerifierService = Depends(get_verifier_service),
) -> list[VerifierHistoryRead]:
    try:
        return await service.get_history(tenant_id, agent_id, conversation_id, limit=limit)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics", response_model=VerifierMetricsSnapshot)
async def get_verifier_metrics(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID | None = Query(default=None),
    service: VerifierService = Depends(get_verifier_service),
) -> VerifierMetricsSnapshot:
    try:
        return await service.get_metrics(tenant_id, agent_id, conversation_id=conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc
