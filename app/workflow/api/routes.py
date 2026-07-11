"""Workflow REST API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_workflow_service, map_domain_errors
from app.workflow.schemas import (
    AdvanceWorkflowRequest,
    ApproveWorkflowRequest,
    StartWorkflowRequest,
    TestWorkflowRequest,
    ValidateWorkflowRequest,
    WorkflowAuditRead,
    WorkflowCreate,
    WorkflowExecutionRead,
    WorkflowMetricsSnapshot,
    WorkflowRead,
    WorkflowStepResult,
)
from app.workflow.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("", response_model=WorkflowStepResult)
async def start_workflow(
    tenant_id: UUID,
    agent_id: UUID,
    body: StartWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStepResult:
    """Start a workflow execution after Planner and Verifier."""
    try:
        return await service.start(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/definitions", response_model=WorkflowRead)
async def create_workflow_definition(
    tenant_id: UUID,
    body: WorkflowCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    try:
        payload = body.model_copy(update={"definition": {**body.definition, "slug": body.slug}})
        return await service.create_workflow(tenant_id, payload)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("", response_model=list[WorkflowRead])
async def list_workflows(
    tenant_id: UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRead]:
    try:
        return await service.list_workflows(tenant_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/templates", response_model=list[WorkflowRead])
async def list_workflow_templates(
    tenant_id: UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowRead]:
    try:
        return await service.list_workflows(tenant_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/history", response_model=list[WorkflowAuditRead])
async def get_workflow_history(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    service: WorkflowService = Depends(get_workflow_service),
) -> list[WorkflowAuditRead]:
    try:
        return await service.get_history(tenant_id, agent_id, conversation_id, limit=limit)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/metrics/snapshot", response_model=WorkflowMetricsSnapshot)
async def get_workflow_metrics(
    tenant_id: UUID,
    agent_id: UUID,
    conversation_id: UUID | None = Query(default=None),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowMetricsSnapshot:
    try:
        return await service.get_metrics(tenant_id, agent_id, conversation_id=conversation_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionRead)
async def get_workflow_execution(
    tenant_id: UUID,
    agent_id: UUID,
    execution_id: UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowExecutionRead:
    try:
        return await service.get_execution(tenant_id, agent_id, execution_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowRead:
    try:
        return await service.get_workflow(tenant_id, workflow_id)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/advance", response_model=WorkflowStepResult)
async def advance_workflow(
    tenant_id: UUID,
    agent_id: UUID,
    body: AdvanceWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStepResult:
    try:
        return await service.advance(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/approve", response_model=WorkflowStepResult)
async def approve_workflow(
    tenant_id: UUID,
    agent_id: UUID,
    body: ApproveWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStepResult:
    try:
        return await service.approve(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/test", response_model=WorkflowStepResult)
async def test_workflow(
    tenant_id: UUID,
    agent_id: UUID,
    body: TestWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowStepResult:
    try:
        return await service.test(tenant_id, agent_id, body)
    except Exception as exc:
        raise map_domain_errors(exc) from exc


@router.post("/validate")
async def validate_workflow(
    body: ValidateWorkflowRequest,
    service: WorkflowService = Depends(get_workflow_service),
) -> dict:
    try:
        violations = await service.validate(body)
        return {"valid": not violations, "violations": violations}
    except Exception as exc:
        raise map_domain_errors(exc) from exc
