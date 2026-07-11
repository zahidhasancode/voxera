import { cn } from "@/lib/cn";

export interface TimelineItem {
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  icon?: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
}

interface TimelineProps {
  items: TimelineItem[];
  className?: string;
}

const dotColors = {
  default: "bg-muted-foreground",
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-destructive",
  info: "bg-info",
};

export function Timeline({ items, className }: TimelineProps) {
  return (
    <ol className={cn("relative space-y-0", className)} aria-label="Timeline">
      {items.map((item, i) => (
        <li key={item.id} className="relative flex gap-4 pb-6 last:pb-0">
          {i < items.length - 1 && (
            <span
              className="absolute left-[7px] top-4 h-[calc(100%-4px)] w-px bg-border"
              aria-hidden
            />
          )}
          <span
            className={cn(
              "relative z-10 mt-1.5 h-3.5 w-3.5 shrink-0 rounded-full ring-4 ring-card",
              dotColors[item.variant ?? "default"],
            )}
            aria-hidden
          />
          <div className="min-w-0 flex-1 pt-0.5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-medium text-foreground">{item.title}</p>
              <time className="text-2xs tabular-nums text-muted-foreground">{item.timestamp}</time>
            </div>
            {item.description && (
              <p className="mt-0.5 text-sm text-muted-foreground">{item.description}</p>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
