import { AlertTriangle } from "lucide-react";

interface UsageProgressBarProps {
  label: string;
  used: number;
  limit: number;
  unit: string;
  /** Show warning state when over this fraction (0–1). Default 0.8 */
  warningThreshold?: number;
  /** Link or button to upgrade (e.g. when near/over limit) */
  upgradeCta?: React.ReactNode;
}

export function UsageProgressBar({
  label,
  used,
  limit,
  unit,
  warningThreshold = 0.8,
  upgradeCta,
}: UsageProgressBarProps) {
  const isUnlimited = limit <= 0;
  const ratio = isUnlimited ? 0.5 : Math.min(1, used / limit);
  const isOver = !isUnlimited && used >= limit;
  const isWarning = !isUnlimited && ratio >= warningThreshold && !isOver;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{label}</span>
          {(isWarning || isOver) && (
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          )}
        </div>
        <div className="text-right">
          <span className="font-semibold tabular-nums text-white">
            {used.toLocaleString()}
          </span>
          {!isUnlimited && (
            <span className="text-sm text-muted-foreground">
              {" "}/ {limit.toLocaleString()} {unit}
            </span>
          )}
          {isUnlimited && (
            <span className="text-sm text-muted-foreground"> {unit}</span>
          )}
        </div>
      </div>
      {!isUnlimited && (
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-border">
          <div
            className={`h-full rounded-full transition-all ${
              isOver
                ? "bg-red-500"
                : isWarning
                ? "bg-amber-500"
                : "bg-primary"
            }`}
            style={{ width: `${Math.min(100, ratio * 100)}%` }}
          />
        </div>
      )}
      {(isWarning || isOver) && upgradeCta && (
        <div className="mt-3">{upgradeCta}</div>
      )}
    </div>
  );
}
