import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Wrench } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Switch } from "@/components/ui/Switch";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableEmptyRow,
} from "@/components/ui/Table";
import { listTools } from "@/lib/api/tools";
import { mapTool } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";
import { useTenantId } from "@/hooks/useTenantId";

export function ToolRegistry() {
  const tenantId = useTenantId();
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: queryKeys.tools(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const res = await listTools(tenantId!);
      return res.items.map(mapTool);
    },
  });

  const tools = data ?? [];
  const filtered = tools.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.slug.toLowerCase().includes(search.toLowerCase()),
  );

  const statusVariant = {
    healthy: "success" as const,
    degraded: "warning" as const,
    disabled: "default" as const,
  };

  if (!tenantId) {
    return (
      <ErrorState
        title="Tenant not configured"
        description="Link your organization to a tenant to view the tool registry."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Tool registry"
        description="Installed tools, health, latency, executions, and permissions"
      />

      <div className="mb-5 flex flex-wrap items-center gap-4">
        <SearchInput placeholder="Search tools…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span>{tools.filter((t) => t.enabled).length} enabled</span>
          <span>{tools.filter((t) => t.status === "degraded").length} degraded</span>
        </div>
      </div>

      <Card>
        <CardHeader title="Installed tools" description={`${filtered.length} tools`} />
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 rounded-lg" />
              ))}
            </div>
          ) : isError ? (
            <div className="p-5">
              <ErrorState title="Failed to load tools" onRetry={() => refetch()} />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tool</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>24h executions</TableHead>
                  <TableHead>Failures</TableHead>
                  <TableHead>Permissions</TableHead>
                  <TableHead>Enabled</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableEmptyRow colSpan={8} message="No tools registered" />
                ) : (
                  filtered.map((tool) => (
                    <TableRow key={tool.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Wrench className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <p className="font-medium text-foreground">{tool.name}</p>
                            <p className="text-2xs text-muted-foreground">{tool.slug}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{tool.category}</TableCell>
                      <TableCell>
                        <Badge variant={statusVariant[tool.status as keyof typeof statusVariant]}>{tool.status}</Badge>
                      </TableCell>
                      <TableCell className="tabular-nums">{tool.avgLatencyMs ? `${tool.avgLatencyMs}ms` : "—"}</TableCell>
                      <TableCell className="tabular-nums">
                        {tool.executions24h ? tool.executions24h.toLocaleString() : "—"}
                      </TableCell>
                      <TableCell className="tabular-nums">{tool.failures24h || "—"}</TableCell>
                      <TableCell>
                        {tool.permissions.length ? (
                          <div className="flex flex-wrap gap-1">
                            {tool.permissions.map((p: string) => (
                              <Badge key={p} variant="default">
                                {p}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                      <TableCell>
                        <Switch checked={tool.enabled} onChange={() => {}} disabled aria-label={`Toggle ${tool.name}`} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}
