import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
  success: (message: string) => void;
  error: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const styles = {
  success: "border-success/30 bg-success-muted/50 text-success",
  error: "border-destructive/30 bg-destructive-muted/50 text-destructive",
  info: "border-info/30 bg-info-muted/50 text-info",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const add = useCallback(
    (message: string, variant: ToastVariant = "info") => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, message, variant }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss]
  );

  const value = useMemo(
    () => ({
      toast: add,
      success: (m: string) => add(m, "success"),
      error: (m: string) => add(m, "error"),
    }),
    [add]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div
          className="pointer-events-none fixed bottom-4 right-4 z-[100] flex flex-col gap-2"
          aria-live="polite"
        >
          {toasts.map(({ id, message, variant }) => {
            const Icon = icons[variant];
            return (
              <div
                key={id}
                className={`pointer-events-auto flex items-center gap-3 rounded-lg border px-4 py-3 shadow-soft-lg animate-fade-in-up ${styles[variant]}`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className="text-sm font-medium text-foreground">{message}</span>
                <button
                  type="button"
                  onClick={() => dismiss(id)}
                  className="ml-2 rounded p-0.5 opacity-70 hover:opacity-100"
                  aria-label="Dismiss"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            );
          })}
        </div>,
        document.body
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
