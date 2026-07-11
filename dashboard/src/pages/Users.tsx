import { useState } from "react";
import { Mail, UserPlus } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { SearchInput } from "@/components/ui/SearchInput";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableEmptyRow,
} from "@/components/ui/Table";
import { useOrg } from "@/contexts/OrgContext";
import { formatRelativeTime } from "@/lib/format";
import type { OrgRole } from "@/types";

export function Users() {
  const [search, setSearch] = useState("");
  const { members, inviteMember, isLoading } = useOrg();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<OrgRole>("developer");
  const [inviting, setInviting] = useState(false);

  const filtered = members.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()),
  );

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setInviting(true);
    try {
      await inviteMember(inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      setInviteOpen(false);
    } finally {
      setInviting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="User management"
        description="Roles, permissions, RBAC, sessions, and activity"
        actions={
          <Button size="sm" onClick={() => setInviteOpen((v) => !v)}>
            <UserPlus className="h-4 w-4" />
            Invite user
          </Button>
        }
      />

      {inviteOpen && (
        <Card className="mb-5 max-w-lg">
          <CardContent className="p-5">
            <form onSubmit={handleInvite} className="flex flex-wrap items-end gap-3">
              <div className="min-w-[200px] flex-1">
                <label className="mb-1 block text-sm text-muted-foreground">Email</label>
                <input
                  type="email"
                  required
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                  placeholder="colleague@company.com"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-muted-foreground">Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as OrgRole)}
                  className="rounded-lg border border-border bg-background px-3 py-2 text-sm"
                >
                  <option value="owner">Owner</option>
                  <option value="admin">Admin</option>
                  <option value="developer">Developer</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              <Button type="submit" disabled={inviting}>
                {inviting ? "Sending…" : "Send invite"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="mb-5">
        <SearchInput placeholder="Search users…" value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-md" />
      </div>

      <Card>
        <CardHeader title="Team members" description={`${filtered.length} users`} />
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 rounded-lg" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableEmptyRow colSpan={5} message="No team members" />
                ) : (
                  filtered.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar name={user.name} size="sm" />
                          <div>
                            <p className="font-medium text-foreground">{user.name}</p>
                            <p className="text-2xs text-muted-foreground">{user.email}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="default">{user.role}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="success">active</Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatRelativeTime(user.joinedAt)}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" disabled>
                          <Mail className="h-4 w-4" />
                          Manage
                        </Button>
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
