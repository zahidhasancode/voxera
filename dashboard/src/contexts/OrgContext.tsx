import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Organization, OrgMember, OrgInvitation, OrgRole } from "@/types";

interface OrgContextValue {
  currentOrg: Organization | null;
  organizations: Organization[];
  setCurrentOrg: (org: Organization) => void;
  createOrganization: (name: string, slug: string) => Promise<Organization>;
  updateOrgLogo: (orgId: string, logoUrl: string | null) => void;
  members: OrgMember[];
  invitations: OrgInvitation[];
  inviteMember: (email: string, role: OrgRole) => Promise<void>;
  removeMember: (memberId: string) => void;
  updateMemberRole: (memberId: string, role: OrgRole) => void;
  cancelInvitation: (invitationId: string) => void;
  isLoading: boolean;
}

const OrgContext = createContext<OrgContextValue | null>(null);

const MOCK_ORGS: Organization[] = [
  { id: "org_1", name: "Acme Corp", slug: "acme", plan: "business", billingInterval: "month", role: "admin" },
  { id: "org_2", name: "Beta Inc", slug: "beta", plan: "pro", billingInterval: "year", role: "developer" },
];

const MOCK_MEMBERS: OrgMember[] = [
  { id: "mem_1", userId: "usr_1", email: "admin@acme.com", name: "Alex Morgan", role: "admin", joinedAt: "2024-01-10" },
  { id: "mem_2", userId: "usr_2", email: "jordan@acme.com", name: "Jordan Lee", role: "developer", joinedAt: "2024-02-15" },
  { id: "mem_3", userId: "usr_3", email: "casey@acme.com", name: "Casey Kim", role: "viewer", joinedAt: "2024-03-01" },
];

const MOCK_INVITATIONS: OrgInvitation[] = [
  { id: "inv_1", email: "new@acme.com", role: "developer", status: "pending", createdAt: "2024-03-10", inviterName: "Alex Morgan" },
];

export function OrgProvider({ children }: { children: ReactNode }) {
  const [organizations, setOrganizations] = useState<Organization[]>(MOCK_ORGS);
  const [currentOrg, setCurrentOrgState] = useState<Organization | null>(MOCK_ORGS[0] ?? null);
  const [members, setMembers] = useState<OrgMember[]>(MOCK_MEMBERS);
  const [invitations, setInvitations] = useState<OrgInvitation[]>(MOCK_INVITATIONS);
  const [isLoading] = useState(false);

  const setCurrentOrg = useCallback((org: Organization) => {
    setCurrentOrgState(org);
  }, []);

  const updateOrgLogo = useCallback((orgId: string, logoUrl: string | null) => {
    setOrganizations((prev) =>
      prev.map((o) => (o.id === orgId ? { ...o, logoUrl } : o))
    );
    setCurrentOrgState((prev) =>
      prev?.id === orgId ? (prev ? { ...prev, logoUrl } : null) : prev
    );
  }, []);

  const createOrganization = useCallback(async (name: string, slug: string): Promise<Organization> => {
    await new Promise((r) => setTimeout(r, 400));
    const newOrg: Organization = {
      id: `org_${Date.now()}`,
      name,
      slug: slug.toLowerCase().replace(/\s+/g, "-"),
      plan: "free",
      role: "owner",
    };
    setOrganizations((prev) => [...prev, newOrg]);
    setCurrentOrgState(newOrg);
    return newOrg;
  }, []);

  const inviteMember = useCallback(async (email: string, role: OrgRole) => {
    await new Promise((r) => setTimeout(r, 300));
    setInvitations((prev) => [
      ...prev,
      { id: `inv_${Date.now()}`, email, role, status: "pending", createdAt: new Date().toISOString().split("T")[0], inviterName: "You" },
    ]);
  }, []);

  const removeMember = useCallback((memberId: string) => {
    setMembers((prev) => prev.filter((m) => m.id !== memberId));
  }, []);

  const updateMemberRole = useCallback((memberId: string, role: OrgRole) => {
    setMembers((prev) => prev.map((m) => (m.id === memberId ? { ...m, role } : m)));
  }, []);

  const cancelInvitation = useCallback((invitationId: string) => {
    setInvitations((prev) => prev.filter((i) => i.id !== invitationId));
  }, []);

  const value: OrgContextValue = useMemo(
    () => ({
      currentOrg,
      organizations,
      setCurrentOrg,
      createOrganization,
      updateOrgLogo,
      members,
      invitations,
      inviteMember,
      removeMember,
      updateMemberRole,
      cancelInvitation,
      isLoading,
    }),
    [
      currentOrg,
      organizations,
      setCurrentOrg,
      createOrganization,
      updateOrgLogo,
      members,
      invitations,
      inviteMember,
      removeMember,
      updateMemberRole,
      cancelInvitation,
      isLoading,
    ]
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export function useOrg(): OrgContextValue {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error("useOrg must be used within OrgProvider");
  return ctx;
}
