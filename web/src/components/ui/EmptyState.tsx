import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  variant?: "default" | "dashed";
  size?: "default" | "lg";
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
  variant = "default",
  size = "default",
}: EmptyStateProps) {
  const borderClass =
    variant === "dashed"
      ? "border-dashed border-border bg-muted/20"
      : "border-border bg-hover/30";
  const paddingClass = size === "lg" ? "py-16 px-8" : "py-12 px-6";
  const iconSize = size === "lg" ? "h-14 w-14" : "h-12 w-12";
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border text-center ${borderClass} ${paddingClass} ${className}`}
    >
      {icon && (
        <div
          className={`mb-4 flex items-center justify-center rounded-xl bg-muted text-muted-foreground ${iconSize}`}
        >
          {icon}
        </div>
      )}
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
