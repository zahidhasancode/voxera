import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { Organization, OrgMember, OrgInvitation, OrgRole } from "@/types";
import { useAuth } from "@/contexts/AuthContext";
import {
  createOrganization,
  getOrganization,
  inviteUser,
  listOrgUsers,
  type OrganizationRecord,
} from "@/lib/iam";
import { queryKeys } from "@/hooks/queryKeys";

interface OrgContextValue {
  currentOrg: Organization | null;
  organizations: Organization[];
  tenantId: string | null;
  setCurrentOrg: (org: Organization) => void;
  createOrganization: (name: string, slug: string, tenantId: string) => Promise<Organization>;
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

function mapOrg(row: OrganizationRecord, role: OrgRole): Organization {
  return {
    id: row.id,
    name: row.company_name,
    slug: row.slug,
    plan: (row.plan as Organization["plan"]) ?? "free",
    role,
  };
}

export function OrgProvider({ children }: { children: ReactNode }) {
  const { profile, user } = useAuth();
  const queryClient = useQueryClient();
  const orgId = profile?.organization_id ?? null;
  const [invitations] = useState<OrgInvitation[]>([]);

  const orgQuery = useQuery({
    queryKey: queryKeys.org(orgId ?? "none"),
    enabled: Boolean(orgId),
    queryFn: () => getOrganization(orgId!),
  });

  const usersQuery = useQuery({
    queryKey: queryKeys.orgUsers(orgId ?? "none"),
    enabled: Boolean(orgId),
    queryFn: () => listOrgUsers(orgId!),
  });

  const currentOrg = useMemo(() => {
    if (!orgQuery.data || !user) return null;
    return mapOrg(orgQuery.data, (profile?.role_slug ?? user.role) as OrgRole);
  }, [orgQuery.data, user, profile?.role_slug]);

  const organizations = currentOrg ? [currentOrg] : [];

  const members: OrgMember[] = useMemo(
    () =>
      (usersQuery.data ?? []).map((u) => ({
        id: u.id,
        userId: u.id,
        email: u.email,
        name: u.name,
        role: (u.role_slug ?? "viewer") as OrgRole,
        joinedAt: new Date().toISOString().slice(0, 10),
      })),
    [usersQuery.data],
  );

  const tenantId = profile?.tenant_id ?? orgQuery.data?.tenant_id ?? null;

  const setCurrentOrg = useCallback((_org: Organization) => {
    /* single-org session; switching requires re-login with org context */
  }, []);

  const updateOrgLogo = useCallback((orgId: string, logoUrl: string | null) => {
    void orgId;
    void logoUrl;
  }, []);

  const createOrganizationHandler = useCallback(
    async (name: string, slug: string, tenant: string): Promise<Organization> => {
      const row = await createOrganization({
        tenant_id: tenant,
        company_name: name,
        slug,
      });
      await queryClient.invalidateQueries({ queryKey: queryKeys.org(row.id) });
      return mapOrg(row, "owner");
    },
    [queryClient],
  );

  const inviteMember = useCallback(
    async (email: string, role: OrgRole) => {
      if (!orgId) throw new Error("No organization selected");
      await inviteUser(orgId, { email, role_slug: role });
      await queryClient.invalidateQueries({ queryKey: queryKeys.orgUsers(orgId) });
    },
    [orgId, queryClient],
  );

  const removeMember = useCallback((_memberId: string) => {
    /* backend remove user endpoint not exposed in current IAM routes */
  }, []);

  const updateMemberRole = useCallback((_memberId: string, _role: OrgRole) => {
    /* role update via IAM roles API — future integration */
  }, []);

  const cancelInvitation = useCallback((_invitationId: string) => {}, []);

  const value: OrgContextValue = useMemo(
    () => ({
      currentOrg,
      organizations,
      tenantId,
      setCurrentOrg,
      createOrganization: createOrganizationHandler,
      updateOrgLogo,
      members,
      invitations,
      inviteMember,
      removeMember,
      updateMemberRole,
      cancelInvitation,
      isLoading: orgQuery.isLoading || usersQuery.isLoading,
    }),
    [
      currentOrg,
      organizations,
      tenantId,
      setCurrentOrg,
      createOrganizationHandler,
      updateOrgLogo,
      members,
      invitations,
      inviteMember,
      removeMember,
      updateMemberRole,
      cancelInvitation,
      orgQuery.isLoading,
      usersQuery.isLoading,
    ],
  );

  return <OrgContext.Provider value={value}>{children}</OrgContext.Provider>;
}

export function useOrg(): OrgContextValue {
  const ctx = useContext(OrgContext);
  if (!ctx) throw new Error("useOrg must be used within OrgProvider");
  return ctx;
}
