import { cn } from "@/lib/cn";

interface ProgressProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  variant?: "default" | "success" | "warning" | "destructive";
  className?: string;
}

const barColors = {
  default: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
  destructive: "bg-destructive",
};

export function Progress({
  value,
  max = 100,
  label,
  showValue = false,
  variant = "default",
  className,
}: ProgressProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("space-y-1.5", className)}>
      {(label || showValue) && (
        <div className="flex justify-between text-xs">
          {label && <span className="text-muted-foreground">{label}</span>}
          {showValue && <span className="tabular-nums text-foreground">{Math.round(pct)}%</span>}
        </div>
      )}
      <div
        className="h-2 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
      >
        <div
          className={cn("h-full rounded-full transition-all duration-300", barColors[variant])}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
