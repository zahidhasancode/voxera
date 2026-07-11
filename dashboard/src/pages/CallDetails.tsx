import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs } from "@/components/ui/Tabs";
import { Timeline } from "@/components/ui/Timeline";
import { LogViewer } from "@/components/ui/LogViewer";
import { TranscriptPanel } from "@/components/calls/LiveCallComponents";
import { useLiveCallsStore } from "@/stores/liveCallsStore";
import { formatDuration, formatRelativeTime } from "@/lib/format";
import { Button } from "@/components/ui/Button";

export function CallDetails() {
  const { callId } = useParams<{ callId: string }>();
  const call = useLiveCallsStore((s) => s.calls.find((c) => c.id === callId));
  const [activeTab, setActiveTab] = useState("timeline");

  if (!call) {
    return (
      <div className="py-16 text-center">
        <p className="text-muted-foreground">Call not found</p>
        <Link to="/app/live-calls" className="mt-4 inline-block">
          <Button variant="outline">Back to live calls</Button>
        </Link>
      </div>
    );
  }

  const timelineItems = call.transcript.map((line, index) => ({
    id: line.id ?? String(index),
    title: line.role === "user" ? "Customer" : line.role === "agent" ? "Agent" : "System",
    description: line.text,
    timestamp: formatRelativeTime(line.timestamp),
    variant: "default" as const,
  }));

  const logLines = call.transcript.map((line, index) => ({
    id: line.id ?? String(index),
    level: "info" as const,
    message: `[${line.role}] ${line.text}`,
    timestamp: formatRelativeTime(line.timestamp),
  }));

  const filterLog = (keywords: string[]) =>
    logLines.filter((l) => keywords.some((k) => l.message.toLowerCase().includes(k)));

  return (
    <>
      <PageHeader
        title={`Call ${call.id}`}
        description={`${call.customerName} · ${call.agentName} · ${formatDuration(call.durationSec)}`}
        actions={
          <Link to="/app/live-calls">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </Link>
        }
      />

      <Tabs
        activeId={activeTab}
        onChange={setActiveTab}
        tabs={[
          { id: "timeline", label: "Timeline", content: <Timeline items={timelineItems} /> },
          { id: "transcript", label: "Transcript", content: <TranscriptPanel lines={call.transcript} /> },
          { id: "planner", label: "Planner", content: <LogViewer lines={filterLog(["intent", "planner"])} className="max-h-96" /> },
          { id: "verifier", label: "Verifier", content: <LogViewer lines={filterLog(["policy", "verif"])} className="max-h-96" /> },
          { id: "tools", label: "Tools", content: <LogViewer lines={filterLog(["tool", "lookup"])} className="max-h-96" /> },
          { id: "workflow", label: "Workflow", content: <LogViewer lines={filterLog(["approval", "workflow"])} className="max-h-96" /> },
          {
            id: "summary",
            label: "Summary",
            content: (
              <p className="text-sm leading-relaxed text-foreground">
                Customer {call.customerName} inquired about a refund for order #
                {call.memorySnapshot.order_id ?? "unknown"}. Refund amount €
                {call.memorySnapshot.refund_amount ?? "—"} exceeds auto-approval threshold.
                Workflow paused pending supervisor approval.
              </p>
            ),
          },
        ]}
      />
    </>
  );
}
