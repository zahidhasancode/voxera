import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTableToolbar } from "@/components/ui/DataTableToolbar";
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
import { listTenantAuditLogs } from "@/lib/api/audit";
import { mapAuditLog } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";
import { useTenantId } from "@/hooks/useTenantId";

export function AuditLog() {
  const tenantId = useTenantId();
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: queryKeys.audit(tenantId ?? "none"),
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const res = await listTenantAuditLogs(tenantId!);
      return res.items.map(mapAuditLog);
    },
  });

  const entries = data ?? [];
  const filtered = useMemo(
    () =>
      entries.filter((e) => {
        if (!search) return true;
        const q = search.toLowerCase();
        return (
          e.action.toLowerCase().includes(q) ||
          e.actorEmail.toLowerCase().includes(q) ||
          e.actorName.toLowerCase().includes(q)
        );
      }),
    [entries, search],
  );

  if (!tenantId) {
    return (
      <ErrorState
        title="Tenant not configured"
        description="Link your organization to a tenant to view audit logs."
      />
    );
  }

  return (
    <>
      <PageHeader title="Audit log" description="Organization activity and change history" />
      <Card>
        <CardHeader title="Activity" description="Search by action or actor" />
        <CardContent>
          <DataTableToolbar search={search} onSearchChange={setSearch} searchPlaceholder="Search activity…" />
          {isLoading ? (
            <div className="space-y-2 py-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 rounded-lg" />
              ))}
            </div>
          ) : isError ? (
            <ErrorState title="Failed to load audit log" onRetry={() => refetch()} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableEmptyRow colSpan={5} message="No matching entries" />
                ) : (
                  filtered.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell className="whitespace-nowrap text-muted-foreground">
                        {new Date(e.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell className="font-mono text-2xs">{e.action}</TableCell>
                      <TableCell>
                        <div className="font-medium">{e.actorName}</div>
                        <div className="text-2xs text-muted-foreground">{e.actorEmail}</div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {e.resourceType}
                        {e.resourceId && <span className="font-mono text-2xs"> · {e.resourceId}</span>}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-muted-foreground">
                        {e.metadata ? JSON.stringify(e.metadata) : "—"}
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
