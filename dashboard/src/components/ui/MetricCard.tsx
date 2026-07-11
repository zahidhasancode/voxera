import { cn } from "@/lib/cn";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  className?: string;
}

export function MetricCard({
  label,
  value,
  unit,
  change,
  changeType = "neutral",
  className,
}: MetricCardProps) {
  const changeColor = {
    positive: "text-success",
    negative: "text-destructive",
    neutral: "text-muted-foreground",
  }[changeType];

  return (
    <div className={cn("rounded-xl border border-border bg-card p-5", className)}>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="text-3xl font-semibold tabular-nums tracking-tight text-foreground">
          {value}
        </span>
        {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
      </div>
      {change && <p className={cn("mt-1.5 text-xs font-medium", changeColor)}>{change}</p>}
    </div>
  );
}
