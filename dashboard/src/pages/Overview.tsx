import { Bot, GitBranch, Phone, BookOpen, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { MetricCard } from "@/components/ui/MetricCard";
import { Button } from "@/components/ui/Button";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { SystemHealthBadge } from "@/components/dashboard/SystemHealthBadge";
import { LiveIndicator } from "@/components/calls/LiveCallComponents";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { useLiveCallsStore } from "@/stores/liveCallsStore";
import { useOperationsWebSocket } from "@/hooks/useOperationsWebSocket";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useTenantId } from "@/hooks/useTenantId";

export function Overview() {
  useOperationsWebSocket();
  const tenantId = useTenantId();
  const { data, isLoading, isError, refetch } = useDashboardData(tenantId);
  const storeMetrics = useLiveCallsStore((s) => s.metrics);
  const metrics = data?.metrics ?? storeMetrics;
  const activity = data?.activity ?? [];
  const activeCalls = useLiveCallsStore((s) => s.calls.filter((c) => c.status !== "ended").length);

  if (!tenantId) {
    return (
      <ErrorState
        title="Tenant not configured"
        description="Sign in with an organization that has a linked tenant, or create one in Settings."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Enterprise operations overview"
        actions={
          <div className="flex items-center gap-3">
            <LiveIndicator />
            <SystemHealthBadge status={metrics.systemHealth} />
            <Link to="/app/live-calls">
              <Button size="sm">
                <Phone className="h-4 w-4" />
                Live calls
                {activeCalls > 0 && (
                  <span className="ml-1 rounded-full bg-primary-foreground/20 px-1.5 py-0.5 text-2xs">
                    {activeCalls}
                  </span>
                )}
              </Button>
            </Link>
          </div>
        }
      />

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState title="Failed to load dashboard" description="Could not fetch metrics from the API." onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Active calls" value={activeCalls} unit="live" change="Real-time" changeType="neutral" />
            <MetricCard label="Knowledge sources" value={metrics.knowledgeSources} change="From API" changeType="neutral" />
            <MetricCard label="Active agents" value={metrics.activeAgents} change="From API" changeType="neutral" />
            <MetricCard label="Processing success" value={`${metrics.workflowSuccessRate}%`} change="Ready sources" changeType="positive" />
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Avg latency" value={metrics.avgLatencyMs || "—"} unit="ms" />
            <MetricCard label="System health" value={metrics.systemHealth} />
          </div>

          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader
                title="Recent activity"
                description="Audit events from the backend"
                actions={
                  <Link to="/app/audit-log" className="text-sm text-primary hover:underline">
                    View all
                    <ArrowUpRight className="ml-1 inline h-3 w-3" />
                  </Link>
                }
              />
              <CardContent>
                {activity.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No recent activity.</p>
                ) : (
                  <ActivityFeed events={activity} />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader title="Quick links" description="Common operations" />
              <CardContent className="space-y-2">
                {[
                  { to: "/app/agents", icon: Bot, label: "Manage agents" },
                  { to: "/app/knowledge", icon: BookOpen, label: "Knowledge base" },
                  { to: "/app/workflows", icon: GitBranch, label: "Workflows" },
                  { to: "/app/live-calls", icon: Phone, label: "Live calls" },
                ].map(({ to, icon: Icon, label }) => (
                  <Link
                    key={to}
                    to={to}
                    className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted/50"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    {label}
                  </Link>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </>
  );
}
