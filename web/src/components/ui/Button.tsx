import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "outline";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
  className?: string;
  loading?: boolean;
}

const variants = {
  primary:
    "bg-primary text-primary-foreground shadow-soft border-transparent hover:opacity-90 hover:shadow-soft-lg active:shadow-inner-soft",
  secondary:
    "bg-muted/50 text-foreground border border-border hover:bg-muted hover:border-muted-foreground/30",
  outline:
    "bg-transparent text-foreground border border-border hover:bg-hover hover:border-muted-foreground/30",
  ghost:
    "bg-transparent text-muted-foreground border-transparent hover:bg-hover hover:text-foreground",
  danger:
    "bg-destructive text-primary-foreground border-transparent hover:opacity-90 shadow-soft",
};

const sizes = {
  sm: "h-8 px-3 text-sm rounded-lg",
  md: "h-10 px-4 text-sm rounded-lg",
  lg: "h-11 px-6 text-sm rounded-lg",
};

export function Button({
  variant = "primary",
  size = "md",
  children,
  className = "",
  disabled,
  loading = false,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 border font-medium transition-all duration-150 ease-smooth focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}
