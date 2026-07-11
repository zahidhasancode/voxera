"""Enterprise multi-tenant REST API router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    audit_logs,
    configurations,
    knowledge_bases,
    tenants,
    tools,
)
from app.knowledge.api.routes import router as knowledge_ingestion_router
from app.rag.api.routes import router as rag_router
from app.memory.api.routes import router as memory_router
from app.planner.api.routes import router as planner_router
from app.verifier.api.routes import router as verifier_router
from app.workflow.api.routes import router as workflow_router
from app.tools.api.routes import router as tool_execution_router
from app.integrations.api.routes import router as integrations_router

enterprise_router = APIRouter()

enterprise_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])

enterprise_router.include_router(
    agents.router,
    prefix="/tenants/{tenant_id}/agents",
    tags=["agents"],
)

enterprise_router.include_router(
    configurations.router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/configuration",
    tags=["configuration"],
)

enterprise_router.include_router(
    knowledge_bases.router,
    prefix="/tenants/{tenant_id}/knowledge-bases",
    tags=["knowledge-bases"],
)

enterprise_router.include_router(
    knowledge_ingestion_router,
    prefix="/tenants/{tenant_id}/knowledge",
    tags=["knowledge"],
)

enterprise_router.include_router(
    rag_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/rag",
    tags=["rag"],
)

enterprise_router.include_router(
    memory_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/memory",
    tags=["memory"],
)

enterprise_router.include_router(
    planner_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/planner",
    tags=["planner"],
)

enterprise_router.include_router(
    verifier_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/verifier",
    tags=["verifier"],
)

enterprise_router.include_router(
    workflow_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/workflow",
    tags=["workflow"],
)

enterprise_router.include_router(
    tool_execution_router,
    prefix="/tenants/{tenant_id}/agents/{agent_id}/tools",
    tags=["tool-execution"],
)

enterprise_router.include_router(
    tools.router,
    prefix="/tenants/{tenant_id}/tools",
    tags=["tools"],
)

enterprise_router.include_router(
    audit_logs.router,
    prefix="/tenants/{tenant_id}/audit-logs",
    tags=["audit"],
)

enterprise_router.include_router(
    integrations_router,
    prefix="/tenants/{tenant_id}/integrations",
    tags=["integrations"],
)
