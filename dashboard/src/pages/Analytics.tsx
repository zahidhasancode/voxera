import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import {
  Clock,
  DollarSign,
  MessageSquare,
  Mic,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/Badge";

/* Theme-aware chart styles – use semantic tokens */
const CHART_STYLE = {
  grid: { stroke: "var(--border)" },
  axis: { stroke: "var(--muted-foreground)", fontSize: 12 },
  tooltip: {
    contentStyle: {
      background: "var(--card)",
      border: "1px solid var(--border)",
      borderRadius: "8px",
    },
    labelStyle: { color: "var(--muted-foreground)" },
  },
};

const MOCK_OVERVIEW = {
  activeConversations: 12,
  voiceMinutesUsed: 3240,
  avgLatencyMs: 142,
  successRate: 98.2,
  costPerConversation: 0.24,
};

const MOCK_USAGE_OVER_TIME = [
  { date: "Mar 1", voiceMinutes: 98, conversations: 45 },
  { date: "Mar 4", voiceMinutes: 112, conversations: 52 },
  { date: "Mar 7", voiceMinutes: 105, conversations: 48 },
  { date: "Mar 10", voiceMinutes: 134, conversations: 61 },
  { date: "Mar 13", voiceMinutes: 128, conversations: 58 },
  { date: "Mar 16", voiceMinutes: 145, conversations: 67 },
  { date: "Mar 19", voiceMinutes: 138, conversations: 62 },
  { date: "Mar 22", voiceMinutes: 156, conversations: 71 },
];

const MOCK_REVENUE = [
  { month: "Jan", revenue: 4200, estimate: 4000 },
  { month: "Feb", revenue: 5100, estimate: 5000 },
  { month: "Mar", revenue: 5800, estimate: 6000 },
];

const MOCK_ERROR_RATES = [
  { date: "Mar 1", errorRate: 1.2, failed: 2 },
  { date: "Mar 4", errorRate: 0.8, failed: 1 },
  { date: "Mar 7", errorRate: 1.5, failed: 3 },
  { date: "Mar 10", errorRate: 0.9, failed: 2 },
  { date: "Mar 13", errorRate: 1.1, failed: 2 },
  { date: "Mar 16", errorRate: 0.7, failed: 1 },
];

const MOCK_AGENT_PERFORMANCE = [
  { agent: "Support Agent", conversations: 1240, avgLatency: 138, successRate: 98.5 },
  { agent: "Sales Assistant", conversations: 89, avgLatency: 156, successRate: 97.2 },
  { agent: "Internal FAQ", conversations: 312, avgLatency: 122, successRate: 99.1 },
];

function LiveMonitorMetrics({
  ttft,
  tokensPerSec,
  audioLatencyMs,
}: {
  ttft: number;
  tokensPerSec: number;
  audioLatencyMs: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-3 text-center">
      <div className="rounded-lg bg-hover/50 px-3 py-2">
        <p className="text-2xs text-muted-foreground">TTFT</p>
        <p className="font-mono text-sm font-semibold text-foreground">{ttft} ms</p>
      </div>
      <div className="rounded-lg bg-hover/50 px-3 py-2">
        <p className="text-2xs text-muted-foreground">Tokens/s</p>
        <p className="font-mono text-sm font-semibold text-foreground">{tokensPerSec}</p>
      </div>
      <div className="rounded-lg bg-hover/50 px-3 py-2">
        <p className="text-2xs text-muted-foreground">Audio latency</p>
        <p className="font-mono text-sm font-semibold text-foreground">{audioLatencyMs} ms</p>
      </div>
    </div>
  );
}

export function Analytics() {
  const [streamingText, setStreamingText] = useState("");
  const [tokenStream, setTokenStream] = useState<string[]>([]);
  const [ttsActive, setTtsActive] = useState(false);
  const [liveMetrics] = useState({
    ttft: 124,
    tokensPerSec: 28.4,
    audioLatencyMs: 45,
  });

  useEffect(() => {
    const transcript = "Hello, how can I help you today? I can look up your account or explain our plans.";
    let i = 0;
    const t = setInterval(() => {
      if (i < transcript.length) {
        setStreamingText(transcript.slice(0, i + 1));
        i++;
      } else clearInterval(t);
    }, 40);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const tokens = "Hello , how can I help you today ?".split(" ");
    let j = 0;
    const t = setInterval(() => {
      if (j < tokens.length) {
        setTokenStream((prev) => [...prev, tokens[j]]);
        j++;
      } else {
        setTtsActive(true);
        clearInterval(t);
      }
    }, 120);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Overview, real-time monitor, and performance trends"
      />

      {/* 1. Overview */}
      <section className="mb-8">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Overview
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/20">
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums text-foreground">
                  {MOCK_OVERVIEW.activeConversations}
                </p>
                <p className="text-sm text-muted-foreground">
                  Active conversations
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/20">
                <Mic className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums text-foreground">
                  {MOCK_OVERVIEW.voiceMinutesUsed.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">
                  Voice minutes used
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/20">
                <Clock className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums text-foreground">
                  {MOCK_OVERVIEW.avgLatencyMs} ms
                </p>
                <p className="text-sm text-muted-foreground">
                  Avg latency
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/20">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums text-foreground">
                  {MOCK_OVERVIEW.successRate}%
                </p>
                <p className="text-sm text-muted-foreground">
                  Success rate
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/20">
                <DollarSign className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-semibold tabular-nums text-foreground">
                  ${MOCK_OVERVIEW.costPerConversation.toFixed(2)}
                </p>
                <p className="text-sm text-muted-foreground">
                  Cost per conversation
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 2. Real-Time Live Monitor */}
      <section className="mb-8">
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Real-time live monitor
        </h2>
        <Card>
          <CardHeader
            title="Live session"
            description="Streaming transcript, LLM tokens, and TTS indicator (demo)"
            actions={
              <Badge variant="success" className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
                Live
              </Badge>
            }
          />
          <CardContent className="space-y-4">
            <div>
              <p className="mb-1.5 text-2xs font-medium text-muted-foreground">
                Streaming transcript
              </p>
              <div className="min-h-[3rem] rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm text-foreground">
                {streamingText}
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-primary-light" />
              </div>
            </div>
            <div>
              <p className="mb-1.5 text-2xs font-medium text-muted-foreground">
                LLM token stream
              </p>
              <div className="flex min-h-[2.5rem] flex-wrap gap-1 rounded-lg border border-border bg-background px-3 py-2">
                {tokenStream.map((t, i) => (
                  <span
                    key={i}
                    className="rounded bg-primary/20 px-1.5 py-0.5 font-mono text-2xs text-primary"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <p className="text-2xs font-medium text-muted-foreground">
                  TTS audio
                </p>
                <div
                  className={`flex h-3 w-3 rounded-full ${
                    ttsActive ? "bg-emerald-400 animate-pulse" : "bg-border"
                  }`}
                />
                <span className="text-sm text-muted-foreground">
                  {ttsActive ? "Playing" : "Idle"}
                </span>
              </div>
              <LiveMonitorMetrics
                ttft={liveMetrics.ttft}
                tokensPerSec={liveMetrics.tokensPerSec}
                audioLatencyMs={liveMetrics.audioLatencyMs}
              />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* 3. Charts */}
      <section>
        <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Trends & performance
        </h2>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader
              title="Usage over time"
              description="Voice minutes and conversations (last 30 days)"
            />
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={MOCK_USAGE_OVER_TIME}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid.stroke} />
                    <XAxis dataKey="date" {...CHART_STYLE.axis} />
                    <YAxis yAxisId="left" {...CHART_STYLE.axis} />
                    <YAxis yAxisId="right" orientation="right" {...CHART_STYLE.axis} />
                    <Tooltip {...CHART_STYLE.tooltip} />
                    <Legend />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="voiceMinutes"
                      name="Voice min"
                      stroke="#0d9488"
                      fill="rgba(13, 148, 136, 0.15)"
                      strokeWidth={1.5}
                    />
                    <Area
                      yAxisId="right"
                      type="monotone"
                      dataKey="conversations"
                      name="Conversations"
                      stroke="#6366f1"
                      fill="rgba(99, 102, 241, 0.15)"
                      strokeWidth={1.5}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Revenue estimate"
              description="Monthly revenue vs estimate"
            />
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={MOCK_REVENUE}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid.stroke} />
                    <XAxis dataKey="month" {...CHART_STYLE.axis} />
                    <YAxis {...CHART_STYLE.axis} tickFormatter={(v) => `$${v}`} />
                    <Tooltip {...CHART_STYLE.tooltip} formatter={(v: number) => [`$${v}`, ""]} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue"
                      stroke="#0d9488"
                      strokeWidth={2}
                      dot={{ fill: "#0d9488" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="estimate"
                      name="Estimate"
                      stroke="#71717a"
                      strokeDasharray="4 4"
                      strokeWidth={1.5}
                      dot={{ fill: "#71717a" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Error rates"
              description="Daily error rate (%) and failed calls"
            />
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={MOCK_ERROR_RATES}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid.stroke} />
                    <XAxis dataKey="date" {...CHART_STYLE.axis} />
                    <YAxis yAxisId="left" {...CHART_STYLE.axis} tickFormatter={(v) => `${v}%`} />
                    <YAxis yAxisId="right" orientation="right" {...CHART_STYLE.axis} />
                    <Tooltip {...CHART_STYLE.tooltip} />
                    <Legend />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="errorRate"
                      name="Error rate %"
                      stroke="#eab308"
                      fill="rgba(234, 179, 8, 0.15)"
                      strokeWidth={1.5}
                    />
                    <Area
                      yAxisId="right"
                      type="monotone"
                      dataKey="failed"
                      name="Failed calls"
                      stroke="#ef4444"
                      fill="rgba(239, 68, 68, 0.1)"
                      strokeWidth={1.5}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Agent performance"
              description="Conversations, avg latency (ms), success rate by agent"
            />
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={MOCK_AGENT_PERFORMANCE}
                    layout="vertical"
                    margin={{ left: 80, right: 24 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid.stroke} horizontal={false} />
                    <XAxis type="number" {...CHART_STYLE.axis} />
                    <YAxis type="category" dataKey="agent" width={76} {...CHART_STYLE.axis} />
                    <Tooltip {...CHART_STYLE.tooltip} />
                    <Legend />
                    <Bar dataKey="conversations" name="Conversations" fill="#0d9488" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="avgLatency" name="Avg latency (ms)" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    <Bar dataKey="successRate" name="Success %" fill="#22c55e" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </>
  );
}
