import { useQuery } from "@tanstack/react-query";
import { fetchHealthDeep } from "@/lib/api/health";
import { getKnowledgeStatus } from "@/lib/api/knowledge";
import { listAgents } from "@/lib/api/agents";
import { listTools } from "@/lib/api/tools";
import { listTenantAuditLogs } from "@/lib/api/audit";
import { mapAuditToActivity } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";
import type { DashboardMetrics, ActivityEvent } from "@/types/operations";
import { useLiveCallsStore } from "@/stores/liveCallsStore";

const EMPTY_METRICS: DashboardMetrics = {
  todaysCalls: 0,
  activeCalls: 0,
  aiResolutionRate: 0,
  escalationRate: 0,
  avgCallDurationSec: 0,
  avgLatencyMs: 0,
  costTodayUsd: 0,
  knowledgeSources: 0,
  activeAgents: 0,
  workflowSuccessRate: 0,
  systemHealth: "healthy",
};

export function useDashboardData(tenantId: string | null) {
  return useQuery({
    queryKey: queryKeys.dashboard(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    refetchInterval: 30_000,
    queryFn: async (): Promise<{ metrics: DashboardMetrics; activity: ActivityEvent[] }> => {
      const [health, knowledge, agents, tools, audit] = await Promise.all([
        fetchHealthDeep().catch(() => ({ status: "degraded" })),
        getKnowledgeStatus(tenantId!),
        listAgents(tenantId!),
        listTools(tenantId!),
        listTenantAuditLogs(tenantId!, 0, 20),
      ]);

      const activeCalls = useLiveCallsStore.getState().calls.filter((c) => c.status !== "ended").length;
      const systemHealth =
        health.status === "healthy" || health.status === "ok"
          ? "healthy"
          : health.status === "degraded"
            ? "degraded"
            : "critical";

      const metrics: DashboardMetrics = {
        ...EMPTY_METRICS,
        activeCalls,
        knowledgeSources: knowledge.total_sources,
        activeAgents: agents.items.filter((a) => a.status === "active").length,
        workflowSuccessRate: knowledge.ready
          ? Math.round((knowledge.ready / Math.max(knowledge.total_sources, 1)) * 100)
          : 0,
        systemHealth,
        avgLatencyMs: tools.items.length ? 0 : 0,
      };

      const activity = audit.items.map(mapAuditToActivity);
      useLiveCallsStore.getState().setMetrics(metrics);

      return { metrics, activity };
    },
  });
}
