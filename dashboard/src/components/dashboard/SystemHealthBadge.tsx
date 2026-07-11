import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";

type Health = "healthy" | "degraded" | "critical";

interface SystemHealthBadgeProps {
  status: Health;
  className?: string;
}

const config: Record<Health, { label: string; variant: "success" | "warning" | "error"; icon: typeof CheckCircle2 }> = {
  healthy: { label: "All systems operational", variant: "success", icon: CheckCircle2 },
  degraded: { label: "Degraded performance", variant: "warning", icon: Activity },
  critical: { label: "Critical issues", variant: "error", icon: AlertTriangle },
};

export function SystemHealthBadge({ status, className }: SystemHealthBadgeProps) {
  const { label, variant, icon: Icon } = config[status];
  return (
    <Badge variant={variant} className={cn("gap-1.5", className)}>
      <Icon className="h-3 w-3" aria-hidden />
      {label}
    </Badge>
  );
}
