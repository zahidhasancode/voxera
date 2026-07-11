import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plug, RefreshCw, Unplug } from "lucide-react";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableEmptyRow,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/Table";
import { queryKeys } from "@/hooks/queryKeys";
import { useTenantId } from "@/hooks/useTenantId";
import {
  connectIntegration,
  disconnectIntegration,
  getIntegrationStatus,
  listIntegrationCatalog,
  listIntegrationLogs,
  listIntegrations,
  triggerIntegrationSync,
  type IntegrationConnection,
  type ProviderCatalogEntry,
} from "@/lib/api/integrations";

const healthVariant: Record<string, "success" | "warning" | "default"> = {
  healthy: "success",
  degraded: "warning",
  unhealthy: "default",
  unknown: "default",
};

export function Integrations() {
  const tenantId = useTenantId();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

  const { data: catalog, isLoading: catalogLoading } = useQuery({
    queryKey: queryKeys.integrationCatalog(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: () => listIntegrationCatalog(tenantId!),
  });

  const {
    data: connections,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: queryKeys.integrations(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: () => listIntegrations(tenantId!),
  });

  const { data: logs } = useQuery({
    queryKey: queryKeys.integrationLogs(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: () => listIntegrationLogs(tenantId!),
  });

  const connectMutation = useMutation({
    mutationFn: (provider: ProviderCatalogEntry) =>
      connectIntegration(tenantId!, {
        provider_slug: provider.slug,
        display_name: provider.name,
        config: {},
      }),
    onSuccess: (res) => {
      if (res.authorization_url) {
        window.open(res.authorization_url, "_blank", "noopener,noreferrer");
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations(tenantId!) });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (connectionId: string) => disconnectIntegration(tenantId!, connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations(tenantId!) });
    },
  });

  const syncMutation = useMutation({
    mutationFn: (connectionId: string) =>
      triggerIntegrationSync(tenantId!, { connection_id: connectionId, sync_mode: "incremental" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations(tenantId!) });
    },
  });

  const statusMutation = useMutation({
    mutationFn: (connectionId: string) => getIntegrationStatus(tenantId!, connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.integrations(tenantId!) });
    },
  });

  const items = connections?.items ?? [];
  const filteredCatalog = (catalog ?? []).filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.category.toLowerCase().includes(search.toLowerCase()),
  );

  if (!tenantId) {
    return (
      <ErrorState
        title="Tenant not configured"
        description="Link your organization to a tenant to manage integrations."
      />
    );
  }

  return (
    <>
      <PageHeader
        title="Integrations"
        description="Connect CRM, helpdesk, ecommerce, calendar, email, and knowledge systems"
      />

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader title="Connected apps" description={`${items.length} active connections`} />
          <CardContent>
            <p className="text-2xl font-semibold">{items.filter((c) => c.status === "connected").length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader title="Healthy" description="Connections passing health checks" />
          <CardContent>
            <p className="text-2xl font-semibold text-emerald-600">
              {items.filter((c) => c.health_status === "healthy").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader title="Available providers" description="Enterprise catalog" />
          <CardContent>
            <p className="text-2xl font-semibold">{catalog?.length ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <div className="mb-6">
        <SearchInput
          placeholder="Search providers by name or category…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-md"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Connected apps" description="Sync status and connection health" />
          <CardContent className="p-0">
            {isLoading ? (
              <div className="space-y-2 p-5">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-lg" />
                ))}
              </div>
            ) : isError ? (
              <div className="p-5">
                <ErrorState title="Failed to load integrations" onRetry={() => refetch()} />
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>App</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Health</TableHead>
                    <TableHead>Last sync</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.length === 0 ? (
                    <TableEmptyRow colSpan={5} message="No connected apps yet" />
                  ) : (
                    items.map((conn: IntegrationConnection) => (
                      <TableRow key={conn.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Plug className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{conn.display_name}</p>
                              <p className="text-2xs text-muted-foreground">{conn.provider_slug}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="default">{conn.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={healthVariant[conn.health_status] ?? "default"}>
                            {conn.health_status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleString() : "—"}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => syncMutation.mutate(conn.id)}
                              disabled={syncMutation.isPending}
                            >
                              <RefreshCw className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => statusMutation.mutate(conn.id)}
                            >
                              Health
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => disconnectMutation.mutate(conn.id)}
                              disabled={disconnectMutation.isPending}
                            >
                              <Unplug className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Connect an app" description="Browse the provider catalog" />
          <CardContent className="max-h-[480px] space-y-2 overflow-y-auto">
            {catalogLoading ? (
              Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 rounded-lg" />)
            ) : (
              filteredCatalog.map((provider) => (
                <div
                  key={provider.slug}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div>
                    <p className="font-medium">{provider.name}</p>
                    <p className="text-2xs text-muted-foreground">
                      {provider.category} · {provider.auth_type}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant={selectedProvider === provider.slug ? "primary" : "outline"}
                    onClick={() => {
                      setSelectedProvider(provider.slug);
                      connectMutation.mutate(provider);
                    }}
                    disabled={connectMutation.isPending}
                  >
                    Connect
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Integration logs" description="Connection, sync, and webhook audit trail" />
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Connection</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(logs?.items ?? []).length === 0 ? (
                <TableEmptyRow colSpan={3} message="No integration activity yet" />
              ) : (
                logs!.items.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(log.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>{log.action}</TableCell>
                    <TableCell className="font-mono text-2xs">{log.connection_id ?? "—"}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </>
  );
}
