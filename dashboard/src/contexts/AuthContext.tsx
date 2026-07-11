import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { User, Session, OrgRole } from "@/types";
import {
  fetchMe,
  listPermissions,
  listSessions,
  login as iamLogin,
  logout as iamLogout,
  revokeSession as iamRevokeSession,
  type CurrentUserProfile,
} from "@/lib/iam";
import { getStoredToken } from "@/lib/api/auth";
import { queryKeys } from "@/hooks/queryKeys";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  permissions: string[];
  profile: CurrentUserProfile | null;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
  sessions: Session[];
  fetchSessions: () => void;
  revokeSession: (sessionId: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function mapUser(profile: CurrentUserProfile): User {
  return {
    id: profile.user.id,
    email: profile.user.email,
    name: profile.user.name,
    role: (profile.role_slug ?? profile.user.role_slug ?? "viewer") as OrgRole,
  };
}

function mapSessions(rows: Awaited<ReturnType<typeof listSessions>>): Session[] {
  return rows.map((s, i) => ({
    id: s.id,
    device: s.user_agent ?? "Unknown device",
    location: s.ip_address,
    ip: s.ip_address,
    lastActiveAt: s.last_active_at,
    current: i === 0,
  }));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [permissions, setPermissions] = useState<string[]>([]);

  const hasToken = Boolean(getStoredToken());

  const profileQuery = useQuery({
    queryKey: queryKeys.me,
    enabled: hasToken,
    retry: false,
    queryFn: async () => {
      const [profile, perms] = await Promise.all([
        fetchMe(),
        listPermissions().catch(() => []),
      ]);
      setPermissions(perms.map((p) => p.slug));
      return profile;
    },
  });

  useEffect(() => {
    if (profileQuery.data?.user.id) {
      listSessions(profileQuery.data.user.id)
        .then(mapSessions)
        .then(setSessions)
        .catch(() => setSessions([]));
    }
  }, [profileQuery.data?.user.id]);

  const signIn = useCallback(
    async (email: string, password: string) => {
      await iamLogin({ email, password });
      await queryClient.invalidateQueries({ queryKey: queryKeys.me });
    },
    [queryClient],
  );

  const signInWithGoogle = useCallback(async () => {
    throw new Error("Google OAuth is not configured on the backend");
  }, []);

  const signOut = useCallback(async () => {
    await iamLogout();
    setSessions([]);
    setPermissions([]);
    queryClient.clear();
  }, [queryClient]);

  const fetchSessions = useCallback(async () => {
    const userId = profileQuery.data?.user.id;
    if (!userId) return;
    const rows = await listSessions(userId);
    setSessions(mapSessions(rows));
  }, [profileQuery.data?.user.id]);

  const revokeSession = useCallback(
    async (sessionId: string) => {
      await iamRevokeSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    },
    [],
  );

  const user = profileQuery.data ? mapUser(profileQuery.data) : null;

  const hasRole = useCallback(
    (...roles: string[]) => {
      if (!user) return false;
      return roles.includes(user.role);
    },
    [user],
  );

  const hasPermission = useCallback(
    (permission: string) => permissions.includes(permission),
    [permissions],
  );

  const value: AuthContextValue = useMemo(
    () => ({
      user,
      isLoading: hasToken && profileQuery.isLoading,
      isAuthenticated: Boolean(user),
      permissions,
      profile: profileQuery.data ?? null,
      signIn,
      signInWithGoogle,
      signOut,
      hasRole,
      hasPermission,
      sessions,
      fetchSessions,
      revokeSession,
    }),
    [
      user,
      hasToken,
      profileQuery.isLoading,
      profileQuery.data,
      permissions,
      signIn,
      signInWithGoogle,
      signOut,
      hasRole,
      hasPermission,
      sessions,
      fetchSessions,
      revokeSession,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
