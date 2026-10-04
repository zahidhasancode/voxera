import {
  authHeaders,
  clearTokens,
  getStoredRefreshToken,
  getStoredToken,
  storeTokens,
} from "./auth";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  tenantId?: string;
  skipAuth?: boolean;
}

function buildUrl(path: string, tenantId?: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (tenantId && !normalized.includes("/tenants/")) {
    return `${API_BASE}/tenants/${tenantId}${normalized}`;
  }
  return `${API_BASE}${normalized}`;
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getStoredRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}/iam/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };
    storeTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function refreshOnce(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
  retried = false,
): Promise<T> {
  const { body, tenantId, headers, skipAuth, ...rest } = options;
  const url = buildUrl(path, tenantId);

  const res = await fetch(url, {
    ...rest,
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(skipAuth ? {} : authHeaders()),
      ...(headers as Record<string, string>),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !skipAuth && !retried && getStoredToken()) {
    const refreshed = await refreshOnce();
    if (refreshed) return apiRequest<T>(path, options, true);
    clearTokens();
  }

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new ApiError(`API ${res.status}: ${res.statusText}`, res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function apiUpload<T>(
  path: string,
  formData: FormData,
  tenantId?: string,
): Promise<T> {
  const url = buildUrl(path, tenantId);
  const res = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new ApiError(`API ${res.status}: ${res.statusText}`, res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "POST", body }),
  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    apiRequest<T>(path, { ...opts, method: "DELETE" }),
};
