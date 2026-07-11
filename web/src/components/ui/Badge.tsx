import type { ReactNode } from "react";

const styles: Record<string, string> = {
  default: "bg-muted text-muted-foreground",
  success: "bg-success-muted text-success",
  warning: "bg-warning-muted text-warning",
  error: "bg-destructive-muted text-destructive",
  primary: "bg-primary-muted text-primary-muted-foreground",
  brand: "bg-primary-muted text-primary-muted-foreground",
  info: "bg-info-muted text-info",
};

interface BadgeProps {
  children: ReactNode;
  variant?: keyof typeof styles;
  className?: string;
}

export function Badge({
  children,
  variant = "default",
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-lg px-2.5 py-0.5 text-2xs font-medium transition-colors duration-150 ${styles[variant] ?? styles.default} ${className}`}
    >
      {children}
    </span>
  );
}
