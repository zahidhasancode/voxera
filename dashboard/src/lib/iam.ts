/** IAM API client for enterprise dashboard integration. */

import { api } from "./api/client";
import { clearTokens, getStoredRefreshToken, storeTokens } from "./api/auth";

export interface LoginRequest {
  email: string;
  password: string;
  organization_id?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: IamUser;
  organization_id?: string;
}

export interface IamUser {
  id: string;
  email: string;
  name: string;
  role_slug?: string;
  department?: string;
  title?: string;
  status: string;
  mfa_enabled: boolean;
}

export interface CurrentUserProfile {
  user: IamUser;
  organization_id: string;
  tenant_id: string | null;
  role_slug: string | null;
  permissions: string[];
}

export interface OrganizationRecord {
  id: string;
  tenant_id: string;
  company_name: string;
  slug: string;
  plan: string;
  status: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  environment: string;
  status: string;
  last_used_at?: string;
}

export interface SessionRecord {
  id: string;
  user_agent?: string;
  ip_address?: string;
  last_active_at: string;
  status: string;
}

export async function login(request: LoginRequest): Promise<AuthTokens> {
  const result = await api.post<AuthTokens>("/iam/auth/login", request, { skipAuth: true });
  storeTokens(result.access_token, result.refresh_token);
  return result;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/iam/auth/logout");
  } finally {
    clearTokens();
  }
}

export async function fetchMe(): Promise<CurrentUserProfile> {
  return api.get<CurrentUserProfile>("/iam/auth/me");
}

export async function listPermissions(): Promise<{ slug: string; name: string; category: string }[]> {
  return api.get("/iam/auth/permissions");
}

export async function getOrganization(orgId: string): Promise<OrganizationRecord> {
  return api.get(`/iam/organizations/${orgId}`);
}

export async function createOrganization(body: {
  tenant_id: string;
  company_name: string;
  slug: string;
  plan?: string;
}): Promise<OrganizationRecord> {
  return api.post("/iam/organizations", body);
}

export async function listOrgUsers(orgId: string): Promise<IamUser[]> {
  return api.get(`/iam/organizations/${orgId}/users`);
}

export async function inviteUser(
  orgId: string,
  invite: { email: string; role_slug: string; department?: string },
): Promise<IamUser> {
  return api.post(`/iam/organizations/${orgId}/users/invite`, invite);
}

export async function listApiKeys(orgId: string): Promise<ApiKey[]> {
  return api.get(`/iam/organizations/${orgId}/api-keys`);
}

export async function createApiKey(
  orgId: string,
  data: { name: string; environment?: string },
): Promise<ApiKey & { secret: string }> {
  return api.post(`/iam/organizations/${orgId}/api-keys`, data);
}

export async function revokeApiKey(orgId: string, keyId: string): Promise<ApiKey> {
  return api.delete(`/iam/organizations/${orgId}/api-keys/${keyId}`);
}

export async function listIamAuditLogs(orgId: string) {
  return api.get(`/iam/organizations/${orgId}/audit-logs`);
}

export async function listSessions(userId: string): Promise<SessionRecord[]> {
  return api.get(`/iam/users/${userId}/sessions`);
}

export async function revokeSession(sessionId: string): Promise<void> {
  await api.delete(`/iam/sessions/${sessionId}`);
}

export async function refreshSession(): Promise<boolean> {
  const refresh = getStoredRefreshToken();
  if (!refresh) return false;
  const result = await api.post<AuthTokens>(
    "/iam/auth/refresh",
    { refresh_token: refresh },
    { skipAuth: true },
  );
  storeTokens(result.access_token, result.refresh_token);
  return true;
}

// Legacy exports for compatibility
export { getStoredToken, clearTokens as clearToken } from "./api/auth";
