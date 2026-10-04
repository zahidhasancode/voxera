import { api } from "./client";

export interface BackendTenant {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedTenants {
  items: BackendTenant[];
  total: number;
  offset: number;
  limit: number;
}

export function listTenants(offset = 0, limit = 100) {
  return api.get<PaginatedTenants>(`/tenants?offset=${offset}&limit=${limit}`);
}

export function createTenant(body: { name: string; slug: string }) {
  return api.post<BackendTenant>("/tenants", body);
}
