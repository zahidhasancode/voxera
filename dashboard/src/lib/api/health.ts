import { api } from "./client";

export interface HealthDeepResponse {
  status: string;
  checks?: Record<string, { status: string; message?: string }>;
}

export async function fetchHealthDeep(): Promise<HealthDeepResponse> {
  return api.get<HealthDeepResponse>("/health/deep");
}

export async function fetchHealthReady(): Promise<{ status: string }> {
  return api.get("/health/ready", { skipAuth: true });
}
