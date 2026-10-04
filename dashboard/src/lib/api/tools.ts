import { api } from "./client";

export interface BackendTool {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  description: string | null;
  tool_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedTools {
  items: BackendTool[];
  total: number;
  offset: number;
  limit: number;
}

export function listTools(tenantId: string, offset = 0, limit = 100) {
  return api.get<PaginatedTools>(`/tools?offset=${offset}&limit=${limit}`, { tenantId });
}
