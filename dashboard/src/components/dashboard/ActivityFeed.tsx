import { Activity, Bot, Phone, Wrench, BookOpen, Shield } from "lucide-react";
import type { ActivityEvent } from "@/types/operations";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/cn";

const icons = {
  call: Phone,
  workflow: Shield,
  tool: Wrench,
  knowledge: BookOpen,
  agent: Bot,
  system: Activity,
};

const severityBorder = {
  info: "border-l-info",
  success: "border-l-success",
  warning: "border-l-warning",
  error: "border-l-destructive",
};

interface ActivityFeedProps {
  events: ActivityEvent[];
  limit?: number;
}

export function ActivityFeed({ events, limit = 8 }: ActivityFeedProps) {
  const shown = events.slice(0, limit);

  return (
    <ul className="divide-y divide-border" aria-label="Recent activity">
      {shown.map((event) => {
        const Icon = icons[event.type];
        return (
          <li
            key={event.id}
            className={cn(
              "flex gap-4 border-l-2 py-4 pl-4 first:pt-0",
              severityBorder[event.severity ?? "info"],
            )}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-4 w-4 text-muted-foreground" aria-hidden />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-foreground">{event.title}</p>
                <time className="shrink-0 text-2xs text-muted-foreground">
                  {formatRelativeTime(event.timestamp)}
                </time>
              </div>
              <p className="mt-0.5 truncate text-sm text-muted-foreground">{event.description}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
