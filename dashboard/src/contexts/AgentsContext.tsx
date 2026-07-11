import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Agent, AgentConfig } from "@/types";
import { useOrg } from "@/contexts/OrgContext";
import {
  createAgent,
  listAgents,
  updateAgent,
} from "@/lib/api/agents";
import { mapAgent } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";

const DEFAULT_CONFIG: AgentConfig = {
  language: "en-US",
  voiceId: "alloy",
  temperature: 0.7,
  toolToggles: {
    knowledge_base: true,
    web_search: false,
    calculator: true,
    code_interpreter: false,
    function_calling: true,
  },
  knowledgeBaseIds: [],
  rateLimits: { requestsPerMinute: 60, concurrentConversations: 10 },
};

function defaultConfig(): AgentConfig {
  return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
}

type AgentsContextValue = {
  agents: Agent[];
  isLoading: boolean;
  error: Error | null;
  getAgentById: (id: string) => Agent | undefined;
  createAgent: (agent: Omit<Agent, "id" | "createdAt" | "updatedAt">) => Promise<Agent>;
  updateAgent: (
    id: string,
    patch: Partial<Agent> & { config?: Partial<AgentConfig> },
  ) => Promise<void>;
  addVersion: (agentId: string, label: string) => void;
  setAgentStatus: (id: string, status: Agent["status"]) => Promise<void>;
  defaultConfig: () => AgentConfig;
};

const AgentsContext = createContext<AgentsContextValue | null>(null);

export function AgentsProvider({ children }: { children: ReactNode }) {
  const { tenantId } = useOrg();
  const queryClient = useQueryClient();

  const agentsQuery = useQuery({
    queryKey: queryKeys.agents(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const res = await listAgents(tenantId!);
      return res.items.map(mapAgent);
    },
  });

  const invalidate = useCallback(() => {
    if (tenantId) {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents(tenantId) });
    }
  }, [queryClient, tenantId]);

  const createMutation = useMutation({
    mutationFn: async (agent: Omit<Agent, "id" | "createdAt" | "updatedAt">) => {
      if (!tenantId) throw new Error("Tenant not configured");
      const config = agent.config ?? defaultConfig();
      const row = await createAgent(tenantId, {
        name: agent.name,
        description: agent.description,
        system_prompt: agent.description || `You are ${agent.name}, a helpful voice assistant.`,
        voice: config.voiceId,
        language: config.language,
        temperature: config.temperature,
        status: agent.status,
      });
      return mapAgent(row);
    },
    onSuccess: invalidate,
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      id,
      patch,
    }: {
      id: string;
      patch: Partial<Agent> & { config?: Partial<AgentConfig> };
    }) => {
      if (!tenantId) throw new Error("Tenant not configured");
      const body: Record<string, unknown> = {};
      if (patch.name) body.name = patch.name;
      if (patch.description !== undefined) body.description = patch.description;
      if (patch.status) body.status = patch.status;
      if (patch.config) {
        if (patch.config.voiceId) body.voice = patch.config.voiceId;
        if (patch.config.language) body.language = patch.config.language;
        if (patch.config.temperature !== undefined) body.temperature = patch.config.temperature;
      }
      await updateAgent(tenantId, id, body);
    },
    onSuccess: invalidate,
  });

  const agents = agentsQuery.data ?? [];

  const getAgentById = useCallback((id: string) => agents.find((a) => a.id === id), [agents]);

  const createAgentHandler = useCallback(
    async (agent: Omit<Agent, "id" | "createdAt" | "updatedAt">) => createMutation.mutateAsync(agent),
    [createMutation],
  );

  const updateAgentHandler = useCallback(
    async (id: string, patch: Partial<Agent> & { config?: Partial<AgentConfig> }) => {
      await updateMutation.mutateAsync({ id, patch });
    },
    [updateMutation],
  );

  const addVersion = useCallback((_agentId: string, _label: string) => {
    /* version history requires backend versioning API */
  }, []);

  const setAgentStatus = useCallback(
    async (id: string, status: Agent["status"]) => {
      await updateAgentHandler(id, { status });
    },
    [updateAgentHandler],
  );

  const value = useMemo<AgentsContextValue>(
    () => ({
      agents,
      isLoading: agentsQuery.isLoading,
      error: agentsQuery.error as Error | null,
      getAgentById,
      createAgent: createAgentHandler,
      updateAgent: updateAgentHandler,
      addVersion,
      setAgentStatus,
      defaultConfig,
    }),
    [
      agents,
      agentsQuery.isLoading,
      agentsQuery.error,
      getAgentById,
      createAgentHandler,
      updateAgentHandler,
      addVersion,
      setAgentStatus,
    ],
  );

  return <AgentsContext.Provider value={value}>{children}</AgentsContext.Provider>;
}

export function useAgents() {
  const ctx = useContext(AgentsContext);
  if (!ctx) throw new Error("useAgents must be used within AgentsProvider");
  return ctx;
}
