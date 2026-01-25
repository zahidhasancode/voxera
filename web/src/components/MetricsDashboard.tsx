import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useVoxera } from "@/store/VoxeraContext";

function LatencyBadge({ ms, label }: { ms: number; label: string }) {
  const color =
    ms < 200 ? "text-latency-good" : ms < 500 ? "text-latency-warn" : "text-latency-bad";
  return (
    <div className="flex flex-col">
      <span className={`text-lg font-mono font-semibold ${color}`}>{Math.round(ms)}</span>
      <span className="text-xs text-voxera-muted">{label}</span>
    </div>
  );
}

export function MetricsDashboard() {
  const {
    lastLlmMetrics,
    lastTtsMetrics,
    llmMetricHistory,
    ttsMetricHistory,
  } = useVoxera();

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
  const ttsChart = ttsMetricHistory.map((m, i) => ({
    i,
    ttfa: m.time_to_first_audio_ms,
    fps: m.frames_per_second,
  }));

  return (
    <section className="rounded-xl border border-voxera-border bg-voxera-surface overflow-hidden">
      <div className="px-4 py-3 border-b border-voxera-border bg-voxera-surface-elevated">
        <h2 className="text-sm font-semibold text-slate-200">Metrics</h2>
      </div>
      <div className="p-4 space-y-6">
        {/* LLM */}
        <div>
          <h3 className="text-xs font-medium text-voxera-muted uppercase tracking-wider mb-2">
            LLM
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
            <LatencyBadge ms={llm.time_to_first_token_ms} label="TTFT (ms)" />
            <LatencyBadge ms={llm.total_generation_ms} label="Total (ms)" />
            <div className="flex flex-col">
              <span className="text-lg font-mono font-semibold text-white">
                {llm.tokens_per_second.toFixed(1)}
              </span>
              <span className="text-xs text-voxera-muted">tokens/s</span>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-mono font-semibold text-white">{llm.token_count}</span>
              <span className="text-xs text-voxera-muted">tokens</span>
            </div>
          </div>
          {llmChart.length > 0 && (
            <div className="h-[80px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={llmChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="i" hide />
                  <YAxis hide domain={["auto", "auto"]} />
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
                    formatter={(v: number) => [v?.toFixed(1), ""]}
                    labelFormatter={(i) => `#${i}`}
                  />
                  <Area type="monotone" dataKey="ttft" stroke="#14b8a6" fill="rgba(20, 184, 166, 0.2)" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* TTS */}
        <div>
          <h3 className="text-xs font-medium text-voxera-muted uppercase tracking-wider mb-2">
            TTS
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
            <LatencyBadge ms={tts.time_to_first_audio_ms} label="TTFA (ms)" />
            <LatencyBadge ms={tts.total_audio_ms} label="Total (ms)" />
            <div className="flex flex-col">
              <span className="text-lg font-mono font-semibold text-white">
                {tts.frames_per_second.toFixed(1)}
              </span>
              <span className="text-xs text-voxera-muted">frames/s</span>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-mono font-semibold text-white">{tts.frame_count}</span>
              <span className="text-xs text-voxera-muted">frames</span>
            </div>
          </div>
          {ttsChart.length > 0 && (
            <div className="h-[80px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={ttsChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="i" hide />
                  <YAxis hide domain={["auto", "auto"]} />
                  <Tooltip
                    contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
                    formatter={(v: number) => [v?.toFixed(1), ""]}
                  />
                  <Area type="monotone" dataKey="ttfa" stroke="#22c55e" fill="rgba(34, 197, 94, 0.2)" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
