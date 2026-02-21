import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = "", ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-muted-foreground">
          {label}
        </label>
      )}
      <input
        className={`w-full rounded-xl border bg-background px-3 py-2 text-sm text-foreground placeholder-muted-foreground transition-colors duration-200 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary ${
          error ? "border-red-500/50" : "border-border hover:border-muted-foreground/50"
        } ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}
