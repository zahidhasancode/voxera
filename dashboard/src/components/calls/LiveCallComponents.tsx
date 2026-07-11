import { motion } from "framer-motion";
import { Phone, PhoneOff, Pause, ArrowRightLeft } from "lucide-react";
import type { LiveCall } from "@/types/operations";
import { formatDuration } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";

interface LiveCallCardProps {
  call: LiveCall;
  selected?: boolean;
  onSelect: () => void;
}

const statusVariant: Record<LiveCall["status"], "success" | "warning" | "info" | "error" | "default"> = {
  active: "success",
  ringing: "warning",
  on_hold: "info",
  transferring: "info",
  ended: "default",
};

export function LiveCallCard({ call, selected, onSelect }: LiveCallCardProps) {
  return (
    <motion.button
      type="button"
      layout
      onClick={onSelect}
      className={cn(
        "w-full rounded-xl border p-4 text-left transition-colors",
        selected
          ? "border-primary bg-primary-muted/20"
          : "border-border bg-card hover:border-border hover:bg-hover/50",
      )}
      aria-pressed={selected}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium text-foreground">{call.customerName}</p>
          <p className="truncate text-xs text-muted-foreground">{call.agentName}</p>
        </div>
        <Badge variant={statusVariant[call.status]}>{call.status.replace("_", " ")}</Badge>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-2xs text-muted-foreground">
        <span>{formatDuration(call.durationSec)}</span>
        <span>{call.language}</span>
        <span>{call.latencyMs}ms</span>
        <span className={call.riskScore > 70 ? "text-warning" : ""}>Risk {call.riskScore}</span>
      </div>
    </motion.button>
  );
}

interface SupervisorControlsProps {
  callId: string;
  onPause: () => void;
  onTransfer: () => void;
  onTerminate: () => void;
}

export function SupervisorControls({ onPause, onTransfer, onTerminate }: SupervisorControlsProps) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Supervisor controls">
      <Button variant="outline" size="sm" onClick={onPause}>
        <Pause className="h-4 w-4" />
        Pause
      </Button>
      <Button variant="outline" size="sm" onClick={onTransfer}>
        <ArrowRightLeft className="h-4 w-4" />
        Transfer
      </Button>
      <Button variant="danger" size="sm" onClick={onTerminate}>
        <PhoneOff className="h-4 w-4" />
        Terminate
      </Button>
    </div>
  );
}

interface TranscriptPanelProps {
  lines: LiveCall["transcript"];
}

export function TranscriptPanel({ lines }: TranscriptPanelProps) {
  return (
    <div className="space-y-3" role="log" aria-live="polite" aria-label="Live transcript">
      {lines.map((line) => (
        <motion.div
          key={line.id}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15 }}
          className={cn(
            "rounded-lg px-3 py-2 text-sm",
            line.role === "user" && "bg-muted text-foreground",
            line.role === "agent" && "bg-primary-muted/30 text-foreground",
            line.role === "system" && "font-mono text-2xs text-muted-foreground",
          )}
        >
          <span className="sr-only">{line.role}: </span>
          {line.text}
        </motion.div>
      ))}
    </div>
  );
}

interface CallStatePanelProps {
  call: LiveCall;
}

export function CallStatePanel({ call }: CallStatePanelProps) {
  const rows = [
    { label: "Intent", value: call.intent },
    { label: "Planner", value: call.plannerState },
    { label: "Workflow", value: call.workflowState },
    { label: "Tool", value: call.currentTool ?? "—" },
    { label: "Risk score", value: String(call.riskScore) },
    { label: "Latency", value: `${call.latencyMs}ms` },
    { label: "Language", value: call.language },
  ];

  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      {rows.map(({ label, value }) => (
        <div key={label} className="rounded-lg border border-border bg-muted/20 px-3 py-2">
          <dt className="text-2xs font-medium uppercase tracking-wide text-muted-foreground">{label}</dt>
          <dd className="mt-0.5 text-sm font-medium text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function LiveIndicator() {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-success">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
      </span>
      Live
    </span>
  );
}

export function CallListEmpty() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Phone className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium text-foreground">No active calls</p>
      <p className="mt-1 text-xs text-muted-foreground">Incoming calls will appear here in real time</p>
    </div>
  );
}
