import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Input } from "@/components/ui/Input";
import type { AuditLogEntry } from "@/types";

const MOCK_ENTRIES: AuditLogEntry[] = [
  { id: "1", action: "member.invited", actorEmail: "admin@acme.com", actorName: "Alex Morgan", resourceType: "invitation", resourceId: "inv_1", metadata: { email: "new@acme.com", role: "developer" }, timestamp: "2024-03-10T14:32:00Z" },
  { id: "2", action: "member.role_updated", actorEmail: "admin@acme.com", actorName: "Alex Morgan", resourceType: "member", resourceId: "mem_2", metadata: { previousRole: "viewer", newRole: "developer" }, timestamp: "2024-03-09T11:20:00Z" },
  { id: "3", action: "api_key.created", actorEmail: "jordan@acme.com", actorName: "Jordan Lee", resourceType: "api_key", resourceId: "key_2", metadata: { name: "Development" }, timestamp: "2024-03-08T09:15:00Z" },
  { id: "4", action: "organization.updated", actorEmail: "admin@acme.com", actorName: "Alex Morgan", resourceType: "organization", resourceId: "org_1", metadata: { field: "name", previous: "Acme", next: "Acme Corp" }, timestamp: "2024-03-07T16:00:00Z" },
  { id: "5", action: "agent.created", actorEmail: "jordan@acme.com", actorName: "Jordan Lee", resourceType: "agent", resourceId: "agt_2", metadata: { name: "Sales Assistant" }, timestamp: "2024-03-06T10:30:00Z" },
];

export function AuditLog() {
  const [entries] = useState<AuditLogEntry[]>(MOCK_ENTRIES);
  const [actionFilter, setActionFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");

  const filtered = entries.filter((e) => {
    if (actionFilter && !e.action.toLowerCase().includes(actionFilter.toLowerCase())) return false;
    if (actorFilter && !e.actorEmail.toLowerCase().includes(actorFilter.toLowerCase()) && !e.actorName.toLowerCase().includes(actorFilter.toLowerCase())) return false;
    return true;
  });

  return (
    <>
      <PageHeader
        title="Audit log"
        description="Organization activity and change history"
      />
      <Card>
        <CardHeader
          title="Activity"
          description="Filter by action or actor"
        />
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Input
              placeholder="Filter by action..."
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="max-w-xs"
            />
            <Input
              placeholder="Filter by actor..."
              value={actorFilter}
              onChange={(e) => setActorFilter(e.target.value)}
              className="max-w-xs"
            />
          </div>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="border-b border-border bg-hover/50 text-left text-sm text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                  <th className="px-4 py-3 font-medium">Resource</th>
                  <th className="px-4 py-3 font-medium">Details</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((e) => (
                  <tr key={e.id} className="border-b border-border/50 text-sm">
                    <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                      {new Date(e.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-2xs text-white">{e.action}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{e.actorName}</div>
                      <div className="text-2xs text-muted-foreground">{e.actorEmail}</div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {e.resourceType}
                      {e.resourceId && <span className="font-mono text-2xs"> · {e.resourceId}</span>}
                    </td>
                    <td className="max-w-[200px] truncate px-4 py-3 text-muted-foreground">
                      {e.metadata ? JSON.stringify(e.metadata) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
