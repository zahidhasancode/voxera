import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import type { ReactNode } from "react";

type AlertVariant = "info" | "success" | "warning" | "error";

interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
  onDismiss?: () => void;
  className?: string;
}

const config = {
  info: { icon: Info, className: "border-info/30 bg-info-muted/30 text-info" },
  success: { icon: CheckCircle2, className: "border-success/30 bg-success-muted/30 text-success" },
  warning: { icon: AlertCircle, className: "border-warning/30 bg-warning-muted/30 text-warning" },
  error: { icon: AlertCircle, className: "border-destructive/30 bg-destructive-muted/30 text-destructive" },
};

export function Alert({
  variant = "info",
  title,
  children,
  onDismiss,
  className = "",
}: AlertProps) {
  const { icon: Icon, className: variantClass } = config[variant];
  return (
    <div
      role="alert"
      className={`flex gap-3 rounded-lg border px-4 py-3 ${variantClass} ${className}`}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0 flex-1">
        {title && <p className="text-sm font-medium text-foreground">{title}</p>}
        <div className={`text-sm text-muted-foreground ${title ? "mt-1" : ""}`}>{children}</div>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded p-1 opacity-70 hover:opacity-100"
          aria-label="Dismiss alert"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
