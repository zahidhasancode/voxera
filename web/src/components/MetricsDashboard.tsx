import { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { useVoxera } from "@/store/VoxeraContext";

function LatencyBadge({ ms, label }: { ms: number; label: string }) {
  const color =
    ms < 200 ? "text-success" : ms < 500 ? "text-warning" : "text-destructive";
  return (
    <div className="flex flex-col">
      <span className={`text-lg font-mono font-semibold tabular-nums ${color}`}>
        {Math.round(ms)}
      </span>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
}

export function MetricsDashboard() {
  const [expanded, setExpanded] = useState(false);
  const { lastLlmMetrics, lastTtsMetrics, llmMetricHistory, ttsMetricHistory } = useVoxera();

  const hasData = llmMetricHistory.length > 0 || ttsMetricHistory.length > 0;

  const llm = lastLlmMetrics ?? {
    time_to_first_token_ms: 0,
    total_generation_ms: 0,
    token_count: 0,
    tokens_per_second: 0,
  };
  const tts = lastTtsMetrics ?? {
    time_to_first_audio_ms: 0,
    total_audio_ms: 0,
    frame_count: 0,
    frames_per_second: 0,
  };

  const llmChart = llmMetricHistory.map((m, i) => ({
    i,
    ttft: m.time_to_first_token_ms,
    tps: m.tokens_per_second,
  }));

  return (
    <Card>
      <CardHeader
        title="Advanced metrics"
        description="LLM and TTS latency (collapsible)"
        actions={
          <Button variant="ghost" size="sm" onClick={() => setExpanded((e) => !e)}>
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        }
      />
      {expanded && (
        <CardContent className="space-y-6">
          {!hasData ? (
            <EmptyState
              title="No metrics yet"
              description="Start a conversation to see latency data."
              variant="dashed"
            />
          ) : (
            <>
              <div>
                <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">LLM</h3>
                <div className="mb-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <LatencyBadge ms={llm.time_to_first_token_ms} label="TTFT (ms)" />
                  <LatencyBadge ms={llm.total_generation_ms} label="Total (ms)" />
                  <div>
                    <span className="text-lg font-mono font-semibold text-foreground">
                      {llm.tokens_per_second.toFixed(1)}
                    </span>
                    <span className="block text-xs text-muted-foreground">tokens/s</span>
                  </div>
                  <div>
                    <span className="text-lg font-mono font-semibold text-foreground">{llm.token_count}</span>
                    <span className="block text-xs text-muted-foreground">tokens</span>
                  </div>
                </div>
                {llmChart.length > 0 && (
                  <div className="h-40">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={llmChart}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="i" hide />
                        <YAxis stroke="var(--muted-foreground)" fontSize={11} />
                        <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)" }} />
                        <Area type="monotone" dataKey="ttft" stroke="var(--primary)" fill="var(--primary-muted)" name="TTFT" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
              <div>
                <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">TTS</h3>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <LatencyBadge ms={tts.time_to_first_audio_ms} label="TTFA (ms)" />
                  <LatencyBadge ms={tts.total_audio_ms} label="Audio (ms)" />
                  <div>
                    <span className="text-lg font-mono font-semibold text-foreground">{tts.frame_count}</span>
                    <span className="block text-xs text-muted-foreground">frames</span>
                  </div>
                  <div>
                    <span className="text-lg font-mono font-semibold text-foreground">
                      {tts.frames_per_second.toFixed(1)}
                    </span>
                    <span className="block text-xs text-muted-foreground">frames/s</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      )}
    </Card>
  );
}
