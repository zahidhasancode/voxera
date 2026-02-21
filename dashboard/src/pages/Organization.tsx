import { useRef, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "@/components/layout/PageHeader";
import { useOrg } from "@/contexts/OrgContext";
import { useAuth } from "@/contexts/AuthContext";
import { Badge } from "@/components/ui/Badge";
import type { OrgRole } from "@/types";

const ORG_ROLES: { value: OrgRole; label: string }[] = [
  { value: "owner", label: "Owner" },
  { value: "admin", label: "Admin" },
  { value: "developer", label: "Developer" },
  { value: "viewer", label: "Viewer" },
];

export function Organization() {
  const { currentOrg, members, invitations, inviteMember, removeMember, updateMemberRole, cancelInvitation, updateOrgLogo } = useOrg();
  const { user, hasRole } = useAuth();
  const canEdit = hasRole("admin", "owner");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<OrgRole>("viewer");
  const [isInviting, setIsInviting] = useState(false);

  function handleLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !currentOrg) return;
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      updateOrgLogo(currentOrg.id, dataUrl);
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  }

  function handleRemoveLogo() {
    if (currentOrg) updateOrgLogo(currentOrg.id, null);
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setIsInviting(true);
    try {
      await inviteMember(inviteEmail.trim(), inviteRole);
      setInviteEmail("");
      setInviteRole("viewer");
    } finally {
      setIsInviting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Organization"
        description="Profile and membership. Owners and admins can manage members."
      />
      <Card className="mb-6">
        <CardHeader
          title="Profile"
          description="Visible to all members. Only owners and admins can edit."
        />
        <CardContent className="space-y-6">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
              Organization logo
            </label>
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border bg-background">
                {currentOrg?.logoUrl ? (
                  <img
                    src={currentOrg.logoUrl}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-2xs text-muted-foreground">
                    No logo
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleLogoChange}
                />
                {canEdit && (
                  <>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      Upload logo
                    </Button>
                    {currentOrg?.logoUrl && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRemoveLogo}
                        className="text-muted-foreground"
                      >
                        Remove
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
            {canEdit && (
              <p className="mt-1.5 text-2xs text-muted-foreground">
                PNG, JPG or SVG. Recommended 128×128 or larger.
              </p>
            )}
          </div>
          <Input
            label="Organization name"
            defaultValue={currentOrg?.name}
            disabled={!canEdit}
          />
          <Input
            label="Slug"
            defaultValue={currentOrg?.slug}
            disabled={!canEdit}
          />
          {canEdit && <Button>Save changes</Button>}
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader
          title="Members"
          description="Manage roles: Owner, Admin, Developer, Viewer."
        />
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-sm text-muted-foreground">
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Email</th>
                <th className="px-6 py-3 font-medium">Role</th>
                <th className="px-6 py-3 font-medium">Joined</th>
                <th className="px-6 py-3 font-medium" />
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-border/50 transition-colors hover:bg-background-hover/50"
                >
                  <td className="px-6 py-4 font-medium text-white">{m.name}</td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {m.email}
                  </td>
                  <td className="px-6 py-4">
                    {m.userId === user?.id ? (
                      <Badge variant="brand">{m.role}</Badge>
                    ) : canEdit ? (
                      <select
                        value={m.role}
                        onChange={(e) => updateMemberRole(m.id, e.target.value as OrgRole)}
                        className="rounded border border-border bg-background px-2 py-1 text-sm text-white focus:border-primary focus:outline-none"
                      >
                        {ORG_ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <Badge>{m.role}</Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {m.joinedAt}
                  </td>
                  <td className="px-6 py-4">
                    {m.userId === user?.id ? (
                      <span className="text-2xs text-muted-foreground">You</span>
                    ) : canEdit && m.role !== "owner" ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeMember(m.id)}
                      >
                        Remove
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {canEdit && (
            <div className="border-t border-border p-4">
              <form onSubmit={handleInvite} className="flex flex-wrap items-end gap-3">
                <Input
                  label="Invite by email"
                  type="email"
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="min-w-[200px] flex-1"
                />
                <div className="min-w-[120px]">
                  <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
                    Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value as OrgRole)}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-white focus:border-primary focus:outline-none"
                  >
                    {ORG_ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
                <Button type="submit" disabled={isInviting}>
                  {isInviting ? "Sending…" : "Invite"}
                </Button>
              </form>
            </div>
          )}
        </CardContent>
      </Card>

      {invitations.length > 0 && (
        <Card>
          <CardHeader
            title="Pending invitations"
            description="Invitations not yet accepted"
          />
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border text-left text-sm text-muted-foreground">
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  <th className="px-6 py-3 font-medium">Invited by</th>
                  <th className="px-6 py-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {invitations.filter((i) => i.status === "pending").map((i) => (
                  <tr
                    key={i.id}
                    className="border-b border-border/50"
                  >
                    <td className="px-6 py-4 font-medium text-white">{i.email}</td>
                    <td className="px-6 py-4">
                      <Badge>{i.role}</Badge>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {i.inviterName} · {i.createdAt}
                    </td>
                    <td className="px-6 py-4">
                      {canEdit && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => cancelInvitation(i.id)}
                        >
                          Cancel
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </>
  );
}
