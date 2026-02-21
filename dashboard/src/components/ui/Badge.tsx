import type { ReactNode } from "react";

const styles: Record<string, string> = {
  default: "bg-muted text-muted-foreground",
  success: "bg-emerald-500/15 text-emerald-400",
  warning: "bg-amber-500/15 text-amber-400",
  error: "bg-red-500/15 text-red-400",
  primary: "bg-primary/20 text-primary",
  brand: "bg-primary/20 text-primary", /* alias for primary */
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
