import { create } from "zustand";
import type { DashboardMetrics, LiveCall } from "@/types/operations";
import type { WebSocketStatus } from "@/lib/websocket";

const EMPTY_METRICS: DashboardMetrics = {
  todaysCalls: 0,
  activeCalls: 0,
  aiResolutionRate: 0,
  escalationRate: 0,
  avgCallDurationSec: 0,
  avgLatencyMs: 0,
  costTodayUsd: 0,
  knowledgeSources: 0,
  activeAgents: 0,
  workflowSuccessRate: 0,
  systemHealth: "healthy",
};

interface LiveCallsState {
  calls: LiveCall[];
  selectedCallId: string | null;
  metrics: DashboardMetrics;
  wsStatus: WebSocketStatus;
  setCalls: (calls: LiveCall[]) => void;
  upsertCall: (call: LiveCall) => void;
  removeCall: (callId: string) => void;
  selectCall: (callId: string | null) => void;
  updateTranscript: (callId: string, line: LiveCall["transcript"][0]) => void;
  setMetrics: (metrics: Partial<DashboardMetrics>) => void;
  setWsStatus: (status: WebSocketStatus) => void;
  pauseCall: (callId: string) => void;
  terminateCall: (callId: string) => void;
}

export const useLiveCallsStore = create<LiveCallsState>((set) => ({
  calls: [],
  selectedCallId: null,
  metrics: EMPTY_METRICS,
  wsStatus: "disconnected",

  setCalls: (calls) => set({ calls }),
  upsertCall: (call) =>
    set((s) => {
      const idx = s.calls.findIndex((c) => c.id === call.id);
      if (idx >= 0) {
        const next = [...s.calls];
        next[idx] = call;
        return { calls: next };
      }
      return { calls: [call, ...s.calls], selectedCallId: s.selectedCallId ?? call.id };
    }),
  removeCall: (callId) =>
    set((s) => ({
      calls: s.calls.filter((c) => c.id !== callId),
      selectedCallId: s.selectedCallId === callId ? null : s.selectedCallId,
    })),
  selectCall: (callId) => set({ selectedCallId: callId }),
  updateTranscript: (callId, line) =>
    set((s) => ({
      calls: s.calls.map((c) =>
        c.id === callId ? { ...c, transcript: [...c.transcript, line] } : c,
      ),
    })),
  setMetrics: (partial) => set((s) => ({ metrics: { ...s.metrics, ...partial } })),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  pauseCall: (callId) =>
    set((s) => ({
      calls: s.calls.map((c) =>
        c.id === callId ? { ...c, status: "on_hold" as const } : c,
      ),
    })),
  terminateCall: (callId) =>
    set((s) => ({
      calls: s.calls.filter((c) => c.id !== callId),
      selectedCallId: s.selectedCallId === callId ? null : s.selectedCallId,
      metrics: { ...s.metrics, activeCalls: Math.max(0, s.metrics.activeCalls - 1) },
    })),
}));

export function useSelectedCall(): LiveCall | undefined {
  return useLiveCallsStore((s) => s.calls.find((c) => c.id === s.selectedCallId));
}
