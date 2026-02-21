import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User, Session } from "@/types";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => void;
  hasRole: (...roles: string[]) => boolean;
  sessions: Session[];
  fetchSessions: () => void;
  revokeSession: (sessionId: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const MOCK_USER: User = {
  id: "usr_1",
  email: "admin@acme.com",
  name: "Alex Morgan",
  role: "admin",
};

const MOCK_SESSIONS: Session[] = [
  { id: "sess_1", device: "Chrome on macOS", location: "San Francisco, CA", lastActiveAt: new Date().toISOString(), current: true },
  { id: "sess_2", device: "Safari on iPhone", location: "San Francisco, CA", lastActiveAt: new Date(Date.now() - 86400000).toISOString(), current: false },
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(MOCK_USER);
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<Session[]>(MOCK_SESSIONS);

  const signIn = useCallback(async (email: string, _password: string) => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 600));
    setUser({ ...MOCK_USER, email });
    setSessions((prev) => prev.map((s) => ({ ...s, current: s.id === "sess_1" })));
    setIsLoading(false);
  }, []);

  const signInWithGoogle = useCallback(async () => {
    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 800));
    setUser({ ...MOCK_USER, email: "alex@gmail.com", name: "Alex Morgan" });
    setSessions((prev) => prev.map((s) => ({ ...s, current: s.id === "sess_1" })));
    setIsLoading(false);
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    setSessions([]);
  }, []);

  const hasRole = useCallback(
    (...roles: string[]) => {
      if (!user) return false;
      return roles.includes(user.role);
    },
    [user]
  );

  const fetchSessions = useCallback(() => {
    setSessions(MOCK_SESSIONS);
  }, []);

  const revokeSession = useCallback((sessionId: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
  }, []);

  const value: AuthContextValue = useMemo(
    () => ({
      user,
      isLoading,
      signIn,
      signInWithGoogle,
      signOut,
      hasRole,
      sessions,
      fetchSessions,
      revokeSession,
    }),
    [user, isLoading, signIn, signInWithGoogle, signOut, hasRole, sessions, fetchSessions, revokeSession]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
