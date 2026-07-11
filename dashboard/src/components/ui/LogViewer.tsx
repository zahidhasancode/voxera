import { useEffect, useRef } from "react";
import { cn } from "@/lib/cn";

interface LogViewerProps {
  lines: { id: string; level?: "info" | "warn" | "error" | "debug"; message: string; timestamp?: string }[];
  className?: string;
  autoScroll?: boolean;
}

const levelColors = {
  info: "text-info",
  warn: "text-warning",
  error: "text-destructive",
  debug: "text-muted-foreground",
};

export function LogViewer({ lines, className, autoScroll = true }: LogViewerProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines, autoScroll]);

  return (
    <div
      className={cn(
        "overflow-auto rounded-lg border border-border bg-muted/30 font-mono text-xs",
        className,
      )}
      role="log"
      aria-live="polite"
      aria-relevant="additions"
    >
      <div className="space-y-0.5 p-3">
        {lines.length === 0 ? (
          <p className="text-muted-foreground">No log entries</p>
        ) : (
          lines.map((line) => (
            <div key={line.id} className="flex gap-2 leading-relaxed">
              {line.timestamp && (
                <span className="shrink-0 tabular-nums text-muted-foreground">{line.timestamp}</span>
              )}
              {line.level && (
                <span className={cn("shrink-0 uppercase", levelColors[line.level])}>
                  [{line.level}]
                </span>
              )}
              <span className="text-foreground">{line.message}</span>
            </div>
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
