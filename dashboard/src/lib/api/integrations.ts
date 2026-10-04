import { api } from "./client";

export interface ProviderCatalogEntry {
  slug: string;
  name: string;
  category: string;
  auth_type: string;
  description: string;
  supported_entities: string[];
  docs_url?: string | null;
}

export interface IntegrationConnection {
  id: string;
  tenant_id: string;
  provider_slug: string;
  category: string;
  auth_type: string;
  status: string;
  display_name: string;
  health_status: string;
  last_sync_at: string | null;
  last_health_at: string | null;
  error_message: string | null;
  sync_schedule_cron: string | null;
  supported_entities: string[];
  created_at: string;
  updated_at: string;
}

export interface IntegrationConnectResponse {
  connection: IntegrationConnection;
  authorization_url?: string | null;
  webhook_url?: string | null;
}

export interface IntegrationStatus {
  connection_id: string;
  provider_slug: string;
  status: string;
  health_status: string;
  last_sync_at: string | null;
  latency_ms: number | null;
  message: string | null;
}

export interface IntegrationAuditLog {
  id: string;
  tenant_id: string;
  connection_id: string | null;
  action: string;
  detail: Record<string, unknown> | null;
  created_at: string;
}

export interface PaginatedIntegrations {
  items: IntegrationConnection[];
  total: number;
  offset: number;
  limit: number;
}

export interface PaginatedIntegrationLogs {
  items: IntegrationAuditLog[];
  total: number;
  offset: number;
  limit: number;
}

export function listIntegrationCatalog(tenantId: string) {
  return api.get<ProviderCatalogEntry[]>(`/integrations/catalog`, { tenantId });
}

export function listIntegrations(tenantId: string, offset = 0, limit = 100) {
  return api.get<PaginatedIntegrations>(`/integrations?offset=${offset}&limit=${limit}`, { tenantId });
}

export function connectIntegration(
  tenantId: string,
  body: {
    provider_slug: string;
    display_name: string;
    config?: Record<string, unknown>;
    credentials?: Record<string, unknown>;
    redirect_uri?: string;
  },
) {
  return api.post<IntegrationConnectResponse>(`/integrations/connect`, body, { tenantId });
}

export function disconnectIntegration(tenantId: string, connectionId: string) {
  return api.post<IntegrationConnection>(
    `/integrations/disconnect`,
    { connection_id: connectionId },
    { tenantId },
  );
}

export function getIntegrationStatus(tenantId: string, connectionId: string) {
  return api.get<IntegrationStatus>(`/integrations/status/${connectionId}`, { tenantId });
}

export function triggerIntegrationSync(
  tenantId: string,
  body: { connection_id: string; sync_mode?: string; entity_types?: string[] },
) {
  return api.post(`/integrations/sync`, body, { tenantId });
}

export function listIntegrationLogs(tenantId: string, connectionId?: string, offset = 0, limit = 50) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  if (connectionId) params.set("connection_id", connectionId);
  return api.get<PaginatedIntegrationLogs>(`/integrations/logs?${params}`, { tenantId });
}
