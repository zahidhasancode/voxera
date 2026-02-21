import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
  className?: string;
}

const variants = {
  primary:
    "bg-primary text-primary-foreground shadow-soft border-transparent hover:opacity-90 hover:shadow-soft-lg active:shadow-inner-soft",
  secondary:
    "bg-hover text-foreground border border-border hover:bg-muted",
  ghost:
    "bg-transparent text-muted-foreground border-transparent hover:bg-hover hover:text-foreground",
  danger:
    "bg-red-600/90 text-white border-transparent hover:bg-red-600 shadow-soft",
};

const sizes = {
  sm: "h-8 px-3 text-sm rounded-lg",
  md: "h-9 px-4 text-sm rounded-xl",
  lg: "h-10 px-5 text-sm rounded-xl",
};

export function Button({
  variant = "primary",
  size = "md",
  children,
  className = "",
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={`inline-flex items-center justify-center border font-medium transition-all duration-200 ease-smooth focus-visible:ring-2 focus-visible:ring-primary disabled:pointer-events-none disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
