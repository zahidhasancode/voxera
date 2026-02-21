import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Environment } from "@/types";

interface EnvContextValue {
  environment: Environment;
  setEnvironment: (env: Environment) => void;
}

const EnvContext = createContext<EnvContextValue | null>(null);

export function EnvProvider({ children }: { children: ReactNode }) {
  const [environment, setEnvironmentState] = useState<Environment>("development");

  const setEnvironment = useCallback((env: Environment) => {
    setEnvironmentState(env);
  }, []);

  const value: EnvContextValue = useMemo(
    () => ({ environment, setEnvironment }),
    [environment, setEnvironment]
  );

  return <EnvContext.Provider value={value}>{children}</EnvContext.Provider>;
}

export function useEnv(): EnvContextValue {
  const ctx = useContext(EnvContext);
  if (!ctx) throw new Error("useEnv must be used within EnvProvider");
  return ctx;
}
