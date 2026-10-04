import type { BackendAgent } from "./api/agents";
import type { KnowledgeSource } from "./api/knowledge";
import type { BackendTool } from "./api/tools";
import type { BackendTenant } from "./api/tenants";
import type { BackendAuditLog } from "./api/audit";
import type { IamUser } from "./iam";
import type {
  Agent,
  AgentConfig,
  AuditLogEntry,
  EmbeddingStatus,
  KnowledgeDocument,
} from "@/types";
import type {
  ActivityEvent,
  PlatformUser,
  TenantSummary,
  ToolRegistryEntry,
  WorkflowDefinition,
} from "@/types/operations";
import type { BackendWorkflow } from "./api/workflows";

export function mapAgent(row: BackendAgent): Agent {
  const config: AgentConfig = {
    language: row.language,
    voiceId: row.voice,
    temperature: row.temperature,
    toolToggles: {
      knowledge_base: true,
      web_search: false,
      calculator: false,
      code_interpreter: false,
      function_calling: true,
    },
    knowledgeBaseIds: [],
    rateLimits: { requestsPerMinute: 60, concurrentConversations: 10 },
  };
  return {
    id: row.id,
    name: row.name,
    description: row.description ?? "",
    status: row.status === "archived" ? "paused" : row.status,
    createdAt: row.created_at.slice(0, 10),
    updatedAt: row.updated_at.slice(0, 10),
    config,
  };
}

export function mapKnowledgeSource(row: KnowledgeSource): KnowledgeDocument {
  const ext = row.original_filename?.split(".").pop()?.toLowerCase();
  const embeddingStatus = mapEmbeddingStatus(row.embedding_status, row.status);
  return {
    id: row.id,
    name: row.original_filename ?? row.title,
    fileType: ext === "pdf" ? "pdf" : "txt",
    size: row.file_size_bytes ?? 0,
    uploadedAt: row.created_at,
    embeddingStatus,
    indexingProgress: row.processing_percent ?? row.progress_pct,
    chunkCount: row.chunk_count,
    chunks: [],
  };
}

function mapEmbeddingStatus(embedding: string, status: string): EmbeddingStatus {
  if (status === "failed") return "failed";
  if (embedding === "complete" || status === "ready") return "ready";
  if (status === "processing" || status === "reprocessing") return "indexing";
  return "pending";
}

export function mapTool(row: BackendTool): ToolRegistryEntry {
  return {
    id: row.id,
    slug: row.slug,
    name: row.name,
    category: row.tool_type,
    status: row.status === "active" ? "healthy" : row.status === "disabled" ? "disabled" : "degraded",
    enabled: row.status === "active",
    avgLatencyMs: 0,
    executions24h: 0,
    failures24h: 0,
    permissions: [],
  };
}

export function mapTenant(row: BackendTenant): TenantSummary {
  return {
    id: row.id,
    name: row.name,
    plan: "business",
    status: row.status === "active" ? "active" : "suspended",
    agents: 0,
    knowledgeDocs: 0,
    storageGb: 0,
    usageMinutes: 0,
    apiKeys: 0,
  };
}

export function mapIamUser(row: IamUser): PlatformUser {
  return {
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role_slug ?? "viewer",
    status: row.status === "active" ? "active" : "suspended",
    lastActiveAt: new Date().toISOString(),
    sessions: 0,
  };
}

export function mapAuditLog(row: BackendAuditLog): AuditLogEntry {
  return {
    id: row.id,
    action: row.action,
    actorEmail: row.actor_id ?? "system",
    actorName: row.actor_id ?? "System",
    resourceType: row.resource_type,
    resourceId: row.resource_id ?? undefined,
    metadata: row.metadata ?? undefined,
    timestamp: row.created_at,
  };
}

export function mapAuditToActivity(row: BackendAuditLog): ActivityEvent {
  return {
    id: row.id,
    type: row.resource_type.includes("knowledge")
      ? "knowledge"
      : row.resource_type.includes("agent")
        ? "agent"
        : row.resource_type.includes("tool")
          ? "tool"
          : row.resource_type.includes("workflow")
            ? "workflow"
            : "system",
    title: row.action.replace(/_/g, " "),
    description: `${row.resource_type}${row.resource_id ? ` · ${row.resource_id}` : ""}`,
    timestamp: row.created_at,
    severity: row.action.includes("fail") || row.action.includes("error") ? "error" : "info",
  };
}

export function mapWorkflow(row: BackendWorkflow): WorkflowDefinition {
  const def = row.definition ?? {};
  const rawSteps = (def.steps as Array<{ id?: string; label?: string; type?: string; name?: string }>) ?? [];
  const rules = (def.rules as unknown[]) ?? [];
  const approvalChain = (def.approval_chain as unknown[]) ?? [];
  const escalation = def.escalation_policy as { targets?: string[] } | undefined;

  return {
    id: row.id,
    name: row.name,
    slug: row.slug,
    enabled: row.enabled,
    steps: rawSteps.map((step, index) => ({
      id: step.id ?? String(index),
      label: step.label ?? step.name ?? step.type ?? `Step ${index + 1}`,
      type: step.type ?? "step",
    })),
    rulesCount: rules.length,
    approvalSteps: approvalChain.length,
    escalationTargets: escalation?.targets ?? [],
    lastModified: row.updated_at,
  };
}
