import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Agent, AgentConfig, AgentVersion } from "@/types";

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
  rateLimits: {
    requestsPerMinute: 60,
    concurrentConversations: 10,
  },
};

function defaultConfig(): AgentConfig {
  return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
}

const INITIAL_AGENTS: Agent[] = [
  {
    id: "agt_1",
    name: "Support Agent",
    description: "Handles tier-1 support and routing",
    status: "active",
    createdAt: "2024-01-15",
    updatedAt: "2024-03-01",
    conversationCount: 1240,
    config: {
      ...defaultConfig(),
      language: "en-US",
      voiceId: "echo",
      temperature: 0.6,
      knowledgeBaseIds: ["kb_1", "kb_2"],
    },
    versionHistory: [
      {
        id: "v1",
        version: 1,
        label: "Initial",
        configSnapshot: defaultConfig(),
        createdAt: "2024-01-15T10:00:00Z",
      },
    ],
  },
  {
    id: "agt_2",
    name: "Sales Assistant",
    description: "Qualifies leads and books demos",
    status: "active",
    createdAt: "2024-02-01",
    updatedAt: "2024-02-15",
    conversationCount: 89,
    config: { ...defaultConfig(), temperature: 0.8 },
    versionHistory: [],
  },
  {
    id: "agt_3",
    name: "Internal FAQ",
    description: "Draft — not yet deployed",
    status: "draft",
    createdAt: "2024-03-10",
    config: { ...defaultConfig() },
    versionHistory: [],
  },
];

type AgentsContextValue = {
  agents: Agent[];
  getAgentById: (id: string) => Agent | undefined;
  createAgent: (agent: Omit<Agent, "id" | "createdAt" | "updatedAt">) => Agent;
  updateAgent: (
    id: string,
    patch: Partial<Agent> & { config?: Partial<AgentConfig> }
  ) => void;
  addVersion: (agentId: string, label: string) => void;
  setAgentStatus: (id: string, status: Agent["status"]) => void;
  defaultConfig: () => AgentConfig;
};

const AgentsContext = createContext<AgentsContextValue | null>(null);

export function AgentsProvider({ children }: { children: ReactNode }) {
  const [agents, setAgents] = useState<Agent[]>(INITIAL_AGENTS);

  const getAgentById = useCallback(
    (id: string) => agents.find((a) => a.id === id),
    [agents]
  );

  const createAgent = useCallback(
    (agent: Omit<Agent, "id" | "createdAt" | "updatedAt">) => {
      const id = `agt_${Date.now()}`;
      const now = new Date().toISOString().slice(0, 10);
      const config = agent.config ?? defaultConfig();
      const newAgent: Agent = {
        ...agent,
        id,
        createdAt: now,
        updatedAt: now,
        config,
        versionHistory: [
          {
            id: `ver_${Date.now()}`,
            version: 1,
            label: "Initial",
            configSnapshot: { ...config },
            createdAt: new Date().toISOString(),
          },
        ],
      };
      setAgents((prev) => [...prev, newAgent]);
      return newAgent;
    },
    []
  );

  const updateAgent = useCallback(
    (id: string, patch: Partial<Agent> & { config?: Partial<AgentConfig> }) => {
      setAgents((prev) =>
        prev.map((a) => {
          if (a.id !== id) return a;
          const config = patch.config
            ? { ...(a.config ?? defaultConfig()), ...patch.config }
            : patch.config ?? a.config;
          return {
            ...a,
            ...patch,
            config,
            updatedAt: new Date().toISOString().slice(0, 10),
          };
        })
      );
    },
    []
  );

  const addVersion = useCallback((agentId: string, label: string) => {
    setAgents((prev) =>
      prev.map((a) => {
        if (a.id !== agentId || !a.config) return a;
        const history = a.versionHistory ?? [];
        const version: AgentVersion = {
          id: `ver_${Date.now()}`,
          version: history.length + 1,
          label,
          configSnapshot: { ...a.config },
          createdAt: new Date().toISOString(),
        };
        return {
          ...a,
          versionHistory: [...history, version],
        };
      })
    );
  }, []);

  const setAgentStatus = useCallback((id: string, status: Agent["status"]) => {
    setAgents((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status } : a))
    );
  }, []);

  const value = useMemo<AgentsContextValue>(
    () => ({
      agents,
      getAgentById,
      createAgent,
      updateAgent,
      addVersion,
      setAgentStatus,
      defaultConfig,
    }),
    [
      agents,
      getAgentById,
      createAgent,
      updateAgent,
      addVersion,
      setAgentStatus,
    ]
  );

  return (
    <AgentsContext.Provider value={value}>{children}</AgentsContext.Provider>
  );
}

export function useAgents() {
  const ctx = useContext(AgentsContext);
  if (!ctx) throw new Error("useAgents must be used within AgentsProvider");
  return ctx;
}
