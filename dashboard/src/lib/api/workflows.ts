import { api } from "./client";

export interface BackendWorkflow {
  id: string;
  tenant_id: string;
  slug: string;
  name: string;
  description: string | null;
  version: string;
  enabled: boolean;
  definition: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export function listWorkflows(tenantId: string, agentId: string) {
  return api.get<BackendWorkflow[]>(`/agents/${agentId}/workflow`, { tenantId });
}

export function getWorkflow(tenantId: string, agentId: string, workflowId: string) {
  return api.get<BackendWorkflow>(`/agents/${agentId}/workflow/${workflowId}`, { tenantId });
}
