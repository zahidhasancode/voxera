import { api } from "./client";

export interface BackendAgent {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  system_prompt: string;
  voice: string;
  language: string;
  temperature: number;
  max_reasoning_steps: number;
  planner_model: string | null;
  verifier_model: string | null;
  status: "draft" | "active" | "paused" | "archived";
  created_at: string;
  updated_at: string;
}

export interface PaginatedAgents {
  items: BackendAgent[];
  total: number;
  offset: number;
  limit: number;
}

export function listAgents(tenantId: string, offset = 0, limit = 100) {
  return api.get<PaginatedAgents>(`/agents?offset=${offset}&limit=${limit}`, { tenantId });
}

export function getAgent(tenantId: string, agentId: string) {
  return api.get<BackendAgent>(`/agents/${agentId}`, { tenantId });
}

export function createAgent(
  tenantId: string,
  body: {
    name: string;
    description?: string;
    system_prompt: string;
    voice?: string;
    language?: string;
    temperature?: number;
    status?: string;
  },
) {
  return api.post<BackendAgent>("/agents", { tenant_id: tenantId, ...body }, { tenantId });
}

export function updateAgent(
  tenantId: string,
  agentId: string,
  body: Partial<{
    name: string;
    description: string;
    system_prompt: string;
    voice: string;
    language: string;
    temperature: number;
    status: string;
  }>,
) {
  return api.patch<BackendAgent>(`/agents/${agentId}`, body, { tenantId });
}

export function deleteAgent(tenantId: string, agentId: string) {
  return api.delete(`/agents/${agentId}`, { tenantId });
}
