import type { WorkflowDefinition } from "@/types/operations";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";

interface WorkflowViewerProps {
  workflow: WorkflowDefinition;
}

export function WorkflowViewer({ workflow }: WorkflowViewerProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-foreground">{workflow.name}</h3>
        <Badge variant={workflow.enabled ? "success" : "default"}>
          {workflow.enabled ? "Enabled" : "Disabled"}
        </Badge>
        <span className="text-sm text-muted-foreground">/{workflow.slug}</span>
      </div>

      <div className="relative">
        <div className="absolute left-6 top-0 h-full w-px bg-border" aria-hidden />
        <ol className="space-y-4">
          {workflow.steps.map((step, i) => (
            <li key={step.id} className="relative flex items-start gap-4 pl-0">
              <span
                className={cn(
                  "relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border-2 border-border bg-card text-sm font-semibold text-foreground",
                )}
              >
                {i + 1}
              </span>
              <div className="min-w-0 flex-1 rounded-xl border border-border bg-card p-4">
                <p className="font-medium text-foreground">{step.label}</p>
                <p className="mt-0.5 text-xs capitalize text-muted-foreground">{step.type}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Rules" value={workflow.rulesCount} />
        <Stat label="Approval steps" value={workflow.approvalSteps} />
        <Stat label="Escalation targets" value={workflow.escalationTargets.length} />
      </div>

      {workflow.escalationTargets.length > 0 && (
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">Escalation targets</p>
          <div className="flex flex-wrap gap-2">
            {workflow.escalationTargets.map((t) => (
              <Badge key={t} variant="info">
                {t.replace("_", " ")}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-muted/20 px-4 py-3">
      <p className="text-2xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-foreground">{value}</p>
    </div>
  );
}
