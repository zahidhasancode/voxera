import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ApiKey, ApiUsageLogEntry, ApiRateLimitDisplay, WebhookEndpoint } from "@/types";
import { useAuth } from "@/contexts/AuthContext";
import { useOrg } from "@/contexts/OrgContext";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/iam";
import { queryKeys } from "@/hooks/queryKeys";

type DeveloperContextValue = {
  apiKeys: ApiKey[];
  webhooks: WebhookEndpoint[];
  usageLogs: ApiUsageLogEntry[];
  rateLimits: ApiRateLimitDisplay[];
  isLoading: boolean;
  createKey: (name: string, live: boolean) => Promise<ApiKey>;
  regenerateKey: (id: string) => ApiKey | null;
  revokeKey: (id: string) => Promise<void>;
  addWebhook: (payload: Omit<WebhookEndpoint, "id" | "createdAt" | "signingSecretPrefix">) => WebhookEndpoint;
  deleteWebhook: (id: string) => void;
  toggleWebhook: (id: string, enabled: boolean) => void;
  dismissKeySecret: (id: string) => void;
};

const DeveloperContext = createContext<DeveloperContextValue | null>(null);

function mapApiKey(row: Awaited<ReturnType<typeof listApiKeys>>[0], secret?: string): ApiKey {
  return {
    id: row.id,
    name: row.name,
    prefix: row.key_prefix,
    secret,
    lastUsedAt: row.last_used_at ?? null,
    createdAt: new Date().toISOString().slice(0, 10),
  };
}

export function DeveloperProvider({ children }: { children: ReactNode }) {
  const { currentOrg } = useOrg();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const orgId = currentOrg?.id;

  const keysQuery = useQuery({
    queryKey: queryKeys.apiKeys(orgId ?? "none"),
    enabled: Boolean(orgId),
    queryFn: async () => {
      const rows = await listApiKeys(orgId!);
      return rows.map((r) => mapApiKey(r));
    },
  });

  const invalidate = useCallback(() => {
    if (orgId) queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys(orgId) });
  }, [queryClient, orgId]);

  const createMutation = useMutation({
    mutationFn: async ({ name, live }: { name: string; live: boolean }) => {
      if (!orgId || !user) throw new Error("Organization required");
      const row = await createApiKey(orgId, {
        name,
        environment: live ? "production" : "development",
      });
      return mapApiKey(row, row.secret);
    },
    onSuccess: invalidate,
  });

  const revokeMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!orgId) throw new Error("Organization required");
      await revokeApiKey(orgId, id);
    },
    onSuccess: invalidate,
  });

  const createKey = useCallback(
    async (name: string, live: boolean) => createMutation.mutateAsync({ name, live }),
    [createMutation],
  );

  const revokeKey = useCallback(
    async (id: string) => revokeMutation.mutateAsync(id),
    [revokeMutation],
  );

  const value = useMemo<DeveloperContextValue>(
    () => ({
      apiKeys: keysQuery.data ?? [],
      webhooks: [],
      usageLogs: [],
      rateLimits: [],
      isLoading: keysQuery.isLoading,
      createKey,
      regenerateKey: () => null,
      revokeKey,
      addWebhook: () => {
        throw new Error("Webhooks API is not available on the backend");
      },
      deleteWebhook: () => {},
      toggleWebhook: () => {},
      dismissKeySecret: () => {},
    }),
    [keysQuery.data, keysQuery.isLoading, createKey, revokeKey],
  );

  return <DeveloperContext.Provider value={value}>{children}</DeveloperContext.Provider>;
}

export function useDeveloper() {
  const ctx = useContext(DeveloperContext);
  if (!ctx) throw new Error("useDeveloper must be used within DeveloperProvider");
  return ctx;
}
