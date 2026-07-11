import { Link } from "react-router-dom";
import { ExternalLink, Radio } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import {
  CallListEmpty,
  CallStatePanel,
  LiveCallCard,
  LiveIndicator,
  SupervisorControls,
  TranscriptPanel,
} from "@/components/calls/LiveCallComponents";
import { useLiveCallsStore, useSelectedCall } from "@/stores/liveCallsStore";
import { useOperationsWebSocket } from "@/hooks/useOperationsWebSocket";
import { formatDuration } from "@/lib/format";
import { cn } from "@/lib/cn";

export function LiveCalls() {
  useOperationsWebSocket();
  const calls = useLiveCallsStore((s) => s.calls.filter((c) => c.status !== "ended"));
  const selectedCallId = useLiveCallsStore((s) => s.selectedCallId);
  const selectCall = useLiveCallsStore((s) => s.selectCall);
  const pauseCall = useLiveCallsStore((s) => s.pauseCall);
  const terminateCall = useLiveCallsStore((s) => s.terminateCall);
  const wsStatus = useLiveCallsStore((s) => s.wsStatus);
  const selected = useSelectedCall();

  return (
    <>
      <PageHeader
        title="Live call center"
        description="Real-time monitoring and supervisor controls"
        actions={
          <div className="flex items-center gap-3">
            <Badge variant={wsStatus === "connected" ? "success" : "warning"}>
              <Radio className="mr-1 h-3 w-3" />
              {wsStatus === "connected" ? "Connected" : "Simulated"}
            </Badge>
            <LiveIndicator />
          </div>
        }
      />

      <div className="grid gap-5 lg:grid-cols-12">
        <Card className="lg:col-span-3">
          <CardHeader title="Incoming calls" description={`${calls.length} active`} />
          <CardContent className="space-y-2">
            {calls.length === 0 ? (
              <CallListEmpty />
            ) : (
              calls.map((call) => (
                <LiveCallCard
                  key={call.id}
                  call={call}
                  selected={call.id === selectedCallId}
                  onSelect={() => selectCall(call.id)}
                />
              ))
            )}
          </CardContent>
        </Card>

        <div className="space-y-5 lg:col-span-6">
          {selected ? (
            <>
              <Card>
                <CardHeader
                  title={selected.customerName}
                  description={`${selected.agentName} · ${formatDuration(selected.durationSec)}`}
                  actions={
                    <Link
                      to={`/app/calls/${selected.id}`}
                      className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                    >
                      Full details
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  }
                />
                <CardContent>
                  <TranscriptPanel lines={selected.transcript} />
                </CardContent>
              </Card>
              <Card>
                <CardHeader title="Supervisor controls" />
                <CardContent>
                  <SupervisorControls
                    callId={selected.id}
                    onPause={() => pauseCall(selected.id)}
                    onTransfer={() => {}}
                    onTerminate={() => terminateCall(selected.id)}
                  />
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground">
                Select a call to view transcript and controls
              </CardContent>
            </Card>
          )}
        </div>

        <Card className="lg:col-span-3">
          <CardHeader title="Call state" />
          <CardContent>
            {selected ? (
              <>
                <CallStatePanel call={selected} />
                <div className="mt-4">
                  <p className="mb-2 text-2xs font-medium uppercase tracking-wide text-muted-foreground">
                    Memory snapshot
                  </p>
                  <dl className="space-y-1 rounded-lg border border-border bg-muted/20 p-3 font-mono text-2xs">
                    {Object.entries(selected.memorySnapshot).map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">{k}</dt>
                        <dd className="text-foreground">{v}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <p className={cn("mt-4 text-2xs text-muted-foreground")}>
                  Customer sentiment — coming soon
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No call selected</p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
