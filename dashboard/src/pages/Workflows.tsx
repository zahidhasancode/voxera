import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { GitBranch, Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { WorkflowViewer } from "@/components/workflows/WorkflowViewer";
import { listWorkflows } from "@/lib/api/workflows";
import { mapWorkflow } from "@/lib/mappers";
import { formatRelativeTime } from "@/lib/format";
import { queryKeys } from "@/hooks/queryKeys";
import { useTenantId } from "@/hooks/useTenantId";
import { useAgents } from "@/contexts/AgentsContext";

export function Workflows() {
  const tenantId = useTenantId();
  const { agents } = useAgents();
  const agentId = agents[0]?.id ?? null;
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: queryKeys.workflows(tenantId ?? "none", agentId ?? "none"),
    enabled: Boolean(tenantId && agentId),
    queryFn: async () => {
      const rows = await listWorkflows(tenantId!, agentId!);
      return rows.map(mapWorkflow);
    },
  });

  const workflows = data ?? [];
  const filtered = workflows.filter(
    (w) =>
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.slug.toLowerCase().includes(search.toLowerCase()),
  );
  const selected = workflows.find((w) => w.id === selectedId) ?? filtered[0];

  useEffect(() => {
    if (filtered.length && !selectedId) {
      setSelectedId(filtered[0].id);
    }
  }, [filtered, selectedId]);

  if (!tenantId) {
    return (
      <ErrorState
        title="Tenant not configured"
        description="Link your organization to a tenant to manage workflows."
      />
    );
  }

  if (!agentId) {
    return (
      <>
        <PageHeader title="Workflow manager" description="Visual workflow viewer — steps, approvals, escalations, and rules" />
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<GitBranch className="h-6 w-6" />}
              title="No agents available"
              description="Create an agent first to attach and view workflows."
            />
          </CardContent>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Workflow manager"
        description={`Workflows for agent ${agents[0]?.name ?? agentId}`}
        actions={
          <Button size="sm" disabled>
            <Plus className="h-4 w-4" />
            New workflow
          </Button>
        }
      />

      <div className="mb-5">
        <SearchInput placeholder="Search workflows…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
      </div>

      {isLoading ? (
        <div className="grid gap-5 lg:grid-cols-12">
          <Skeleton className="h-96 rounded-xl lg:col-span-4" />
          <Skeleton className="h-96 rounded-xl lg:col-span-8" />
        </div>
      ) : isError ? (
        <ErrorState title="Failed to load workflows" onRetry={() => refetch()} />
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="p-8">
            <EmptyState
              icon={<GitBranch className="h-6 w-6" />}
              title="No workflows"
              description="No workflow definitions exist for this agent yet."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-5 lg:grid-cols-12">
          <Card className="lg:col-span-4">
            <CardContent className="divide-y divide-border p-0">
              {filtered.map((wf) => (
                <button
                  key={wf.id}
                  type="button"
                  onClick={() => setSelectedId(wf.id)}
                  className={`flex w-full items-start gap-3 px-5 py-4 text-left transition-colors hover:bg-hover ${
                    selected?.id === wf.id ? "bg-primary-muted/20" : ""
                  }`}
                >
                  <GitBranch className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{wf.name}</p>
                      <Badge variant={wf.enabled ? "success" : "default"}>{wf.enabled ? "On" : "Off"}</Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {wf.steps.length} steps · {wf.rulesCount} rules · Updated {formatRelativeTime(wf.lastModified)}
                    </p>
                  </div>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="lg:col-span-8">
            <CardContent className="p-6">
              {selected ? <WorkflowViewer workflow={selected} /> : <p className="text-muted-foreground">Select a workflow</p>}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
