import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  ApiKey,
  ApiUsageLogEntry,
  ApiRateLimitDisplay,
  WebhookEndpoint,
} from "@/types";

const PREFIX_LIVE = "vox_live_";
const PREFIX_TEST = "vox_test_";

function generateSecret(prefix: string): string {
  return prefix + Array.from({ length: 24 }, () =>
    "abcdefghijklmnopqrstuvwxyz0123456789"[Math.floor(Math.random() * 36)]
  ).join("");
}

const INITIAL_KEYS: ApiKey[] = [
  {
    id: "key_1",
    name: "Production",
    prefix: "vox_live_••••••••••••••••••••••••",
    lastUsedAt: "2024-03-15T14:32:00Z",
    createdAt: "2024-01-10",
  },
  {
    id: "key_2",
    name: "Development",
    prefix: "vox_test_••••••••••••••••••••••••",
    lastUsedAt: null,
    createdAt: "2024-02-01",
  },
];

const INITIAL_WEBHOOKS: WebhookEndpoint[] = [
  {
    id: "wh_1",
    url: "https://api.example.com/voxera/events",
    description: "Production events",
    events: ["conversation.completed", "agent.error"],
    signingSecretPrefix: "whsec_••••••••••••",
    createdAt: "2024-02-15",
    enabled: true,
  },
];

const INITIAL_LOGS: ApiUsageLogEntry[] = [
  { id: "log_1", timestamp: "2024-03-20T10:15:00Z", method: "POST", path: "/v1/conversations", status: 201, keyId: "key_1", keyName: "Production", durationMs: 142 },
  { id: "log_2", timestamp: "2024-03-20T10:14:58Z", method: "GET", path: "/v1/agents", status: 200, keyId: "key_1", keyName: "Production", durationMs: 28 },
  { id: "log_3", timestamp: "2024-03-20T10:12:00Z", method: "POST", path: "/v1/conversations/conv_123/messages", status: 200, keyId: "key_1", keyName: "Production", durationMs: 89 },
  { id: "log_4", timestamp: "2024-03-20T09:45:00Z", method: "GET", path: "/v1/agents/agt_1", status: 200, keyId: "key_2", keyName: "Development", durationMs: 31 },
  { id: "log_5", timestamp: "2024-03-20T09:44:00Z", method: "POST", path: "/v1/conversations", status: 429, keyId: "key_2", keyName: "Development", durationMs: 5 },
];

const RATE_LIMITS: ApiRateLimitDisplay[] = [
  { limit: 100, remaining: 87, window: "1 minute", resetsAt: new Date(Date.now() + 45_000).toISOString() },
  { limit: 5000, remaining: 4821, window: "1 hour", resetsAt: new Date(Date.now() + 34 * 60_000).toISOString() },
];

type DeveloperContextValue = {
  apiKeys: ApiKey[];
  webhooks: WebhookEndpoint[];
  usageLogs: ApiUsageLogEntry[];
  rateLimits: ApiRateLimitDisplay[];
  createKey: (name: string, live: boolean) => ApiKey;
  regenerateKey: (id: string) => ApiKey | null;
  revokeKey: (id: string) => void;
  addWebhook: (payload: Omit<WebhookEndpoint, "id" | "createdAt" | "signingSecretPrefix">) => WebhookEndpoint;
  deleteWebhook: (id: string) => void;
  toggleWebhook: (id: string, enabled: boolean) => void;
  dismissKeySecret: (id: string) => void;
};

const DeveloperContext = createContext<DeveloperContextValue | null>(null);

export function DeveloperProvider({ children }: { children: ReactNode }) {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(INITIAL_KEYS);
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>(INITIAL_WEBHOOKS);
  const [usageLogs] = useState<ApiUsageLogEntry[]>(INITIAL_LOGS);
  const [rateLimits] = useState<ApiRateLimitDisplay[]>(RATE_LIMITS);

  const createKey = useCallback((name: string, live: boolean) => {
    const prefix = live ? PREFIX_LIVE : PREFIX_TEST;
    const secret = generateSecret(prefix);
    const id = `key_${Date.now()}`;
    const key: ApiKey = {
      id,
      name,
      prefix: prefix + "••••••••••••••••••••••••",
      secret,
      lastUsedAt: null,
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setApiKeys((prev) => [...prev, key]);
    return key;
  }, []);

  const regenerateKey = useCallback((id: string) => {
    let created: ApiKey | null = null;
    setApiKeys((prev) =>
      prev.map((k) => {
        if (k.id !== id) return k;
        const isLive = k.prefix.startsWith(PREFIX_LIVE);
        const prefix = isLive ? PREFIX_LIVE : PREFIX_TEST;
        const secret = generateSecret(prefix);
        created = {
          ...k,
          prefix: prefix + "••••••••••••••••••••••••",
          secret,
        };
        return created;
      })
    );
    return created ?? null;
  }, []);

  const revokeKey = useCallback((id: string) => {
    setApiKeys((prev) => prev.filter((k) => k.id !== id));
  }, []);

  const dismissKeySecret = useCallback((id: string) => {
    setApiKeys((prev) =>
      prev.map((k) => (k.id === id ? { ...k, secret: undefined } : k))
    );
  }, []);

  const addWebhook = useCallback(
    (payload: Omit<WebhookEndpoint, "id" | "createdAt" | "signingSecretPrefix">) => {
      const id = `wh_${Date.now()}`;
      const endpoint: WebhookEndpoint = {
        ...payload,
        id,
        signingSecretPrefix: "whsec_••••••••••••",
        createdAt: new Date().toISOString().slice(0, 10),
        enabled: true,
      };
      setWebhooks((prev) => [...prev, endpoint]);
      return endpoint;
    },
    []
  );

  const deleteWebhook = useCallback((id: string) => {
    setWebhooks((prev) => prev.filter((w) => w.id !== id));
  }, []);

  const toggleWebhook = useCallback((id: string, enabled: boolean) => {
    setWebhooks((prev) =>
      prev.map((w) => (w.id === id ? { ...w, enabled } : w))
    );
  }, []);

  const value = useMemo<DeveloperContextValue>(
    () => ({
      apiKeys,
      webhooks,
      usageLogs,
      rateLimits,
      createKey,
      regenerateKey,
      revokeKey,
      addWebhook,
      deleteWebhook,
      toggleWebhook,
      dismissKeySecret,
    }),
    [
      apiKeys,
      webhooks,
      usageLogs,
      rateLimits,
      createKey,
      regenerateKey,
      revokeKey,
      addWebhook,
      deleteWebhook,
      toggleWebhook,
      dismissKeySecret,
    ]
  );

  return (
    <DeveloperContext.Provider value={value}>
      {children}
    </DeveloperContext.Provider>
  );
}

export function useDeveloper() {
  const ctx = useContext(DeveloperContext);
  if (!ctx) throw new Error("useDeveloper must be used within DeveloperProvider");
  return ctx;
}
