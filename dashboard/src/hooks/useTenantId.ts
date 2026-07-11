import { useOrg } from "@/contexts/OrgContext";

export function useTenantId(): string | null {
  const { tenantId } = useOrg();
  return tenantId;
}
