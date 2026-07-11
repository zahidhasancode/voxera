import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent } from "./Card";

type Tint = "primary" | "accent" | "info" | "success" | "warning";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  href?: string;
  tint?: Tint;
  trend?: string;
}

const tintClasses: Record<Tint, string> = {
  primary: "bg-primary-muted text-primary-muted-foreground",
  accent: "bg-accent-muted/50 text-accent-muted-foreground dark:bg-accent-muted/30",
  info: "bg-info-muted/80 text-info dark:bg-info-muted/50",
  success: "bg-success-muted text-success dark:bg-success-muted/80",
  warning: "bg-warning-muted text-warning dark:bg-warning-muted/80",
};

export function StatCard({
  label,
  value,
  icon: Icon,
  href,
  tint = "primary",
  trend,
}: StatCardProps) {
  const content = (
    <Card className={href ? "hover-lift transition-all duration-200 group-hover:border-border" : ""}>
      <CardContent className="flex items-center gap-5 p-6">
        <div
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${tintClasses[tint]}`}
        >
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0">
          <p className="text-2xl font-semibold tabular-nums tracking-tight text-foreground">
            {value}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{label}</p>
          {trend && <p className="mt-0.5 text-2xs text-success">{trend}</p>}
        </div>
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <Link to={href} className="group block">
        {content}
      </Link>
    );
  }
  return content;
}
