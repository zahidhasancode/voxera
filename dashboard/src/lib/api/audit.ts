import { api } from "./client";

export interface BackendAuditLog {
  id: string;
  tenant_id: string;
  action: string;
  actor_id: string | null;
  resource_type: string;
  resource_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface PaginatedAuditLogs {
  items: BackendAuditLog[];
  total: number;
  offset: number;
  limit: number;
}

export function listTenantAuditLogs(tenantId: string, offset = 0, limit = 100) {
  return api.get<PaginatedAuditLogs>(`/audit-logs?offset=${offset}&limit=${limit}`, { tenantId });
}
