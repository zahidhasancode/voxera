import type { ReactNode } from "react";

interface SkeletonProps {
  className?: string;
  children?: ReactNode;
}

export function Skeleton({ className = "", children }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-border/60 ${className}`}
      aria-hidden
    >
      {children}
    </div>
  );
}

/** Text line placeholder */
export function SkeletonText({ className = "" }: { className?: string }) {
  return <Skeleton className={`h-4 ${className}`} />;
}

/** Multi-line text block */
export function SkeletonBlock({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={`h-4 ${i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"}`}
        />
      ))}
    </div>
  );
}

/** Table row placeholder */
export function SkeletonRow({ cols = 4 }: { cols?: number }) {
  return (
    <tr className="border-b border-border/50">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-6 py-4">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

/** Card placeholder (title + content blocks) */
export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-border bg-card shadow-soft overflow-hidden">
      <div className="border-b border-border px-6 py-4">
        <Skeleton className="mb-2 h-5 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="space-y-4 p-6">
        <SkeletonBlock lines={3} />
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  );
}
