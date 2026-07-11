import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, MoreHorizontal } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { SearchInput } from "@/components/ui/SearchInput";
import { Progress } from "@/components/ui/Progress";
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
import { listTenants } from "@/lib/api/tenants";
import { mapTenant } from "@/lib/mappers";
import { queryKeys } from "@/hooks/queryKeys";

export function Tenants() {
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: queryKeys.tenants,
    queryFn: async () => {
      const res = await listTenants();
      return res.items.map(mapTenant);
    },
  });

  const tenants = data ?? [];
  const filtered = tenants.filter((t) => t.name.toLowerCase().includes(search.toLowerCase()));

  const statusVariant = {
    active: "success" as const,
    trial: "warning" as const,
    suspended: "error" as const,
  };

  return (
    <>
      <PageHeader
        title="Tenant management"
        description="Companies, plans, usage, storage, agents, and API keys"
      />

      <div className="mb-5">
        <SearchInput placeholder="Search tenants…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState title="Failed to load tenants" description="Could not fetch tenant list from the API." onRetry={() => refetch()} />
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-4">
            {[
              { label: "Total tenants", value: tenants.length },
              { label: "Enterprise", value: tenants.filter((t) => t.plan === "Enterprise").length },
              { label: "Active", value: tenants.filter((t) => t.status === "active").length },
              { label: "Trial", value: tenants.filter((t) => t.status === "trial").length },
            ].map(({ label, value }) => (
              <Card key={label}>
                <CardContent className="p-5">
                  <p className="text-sm text-muted-foreground">{label}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">{value}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader title="Companies" />
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Agents</TableHead>
                    <TableHead>Knowledge</TableHead>
                    <TableHead>Storage</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>API keys</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.length === 0 ? (
                    <TableEmptyRow colSpan={9} message="No tenants found" />
                  ) : (
                    filtered.map((tenant) => (
                      <TableRow key={tenant.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium text-foreground">{tenant.name}</span>
                          </div>
                        </TableCell>
                        <TableCell>{tenant.plan}</TableCell>
                        <TableCell>
                          <Badge variant={statusVariant[tenant.status as keyof typeof statusVariant]}>{tenant.status}</Badge>
                        </TableCell>
                        <TableCell className="tabular-nums">{tenant.agents || "—"}</TableCell>
                        <TableCell className="tabular-nums">{tenant.knowledgeDocs || "—"}</TableCell>
                        <TableCell>
                          <div className="w-24">
                            <Progress value={tenant.storageGb} max={100} showValue variant="default" />
                            <span className="text-2xs text-muted-foreground">{tenant.storageGb ? `${tenant.storageGb} GB` : "—"}</span>
                          </div>
                        </TableCell>
                        <TableCell className="tabular-nums">
                          {tenant.usageMinutes ? `${tenant.usageMinutes.toLocaleString()} min` : "—"}
                        </TableCell>
                        <TableCell className="tabular-nums">{tenant.apiKeys || "—"}</TableCell>
                        <TableCell>
                          <button type="button" className="rounded p-1 hover:bg-hover" aria-label="Actions">
                            <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                          </button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </>
  );
}
