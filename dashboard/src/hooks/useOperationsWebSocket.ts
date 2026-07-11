import { useEffect } from "react";
import { operationsSocket } from "@/lib/websocket";
import { useLiveCallsStore } from "@/stores/liveCallsStore";
import { getStoredToken } from "@/lib/api/auth";
import type { LiveCall } from "@/types/operations";

/** Connect to operations WebSocket and sync live call state from the backend. */
export function useOperationsWebSocket() {
  const setWsStatus = useLiveCallsStore((s) => s.setWsStatus);
  const upsertCall = useLiveCallsStore((s) => s.upsertCall);
  const updateTranscript = useLiveCallsStore((s) => s.updateTranscript);
  const setMetrics = useLiveCallsStore((s) => s.setMetrics);

  useEffect(() => {
    const unsubStatus = operationsSocket.onStatus(setWsStatus);

    const unsubMsg = operationsSocket.subscribe((msg) => {
      if (msg.type === "call_update" && msg.payload) {
        upsertCall(msg.payload as unknown as LiveCall);
      }
      if (msg.type === "transcript_line" && msg.payload) {
        const { callId, line } = msg.payload as { callId: string; line: LiveCall["transcript"][0] };
        updateTranscript(callId, line);
      }
      if (msg.type === "metrics_update" && msg.payload) {
        setMetrics(msg.payload as Partial<ReturnType<typeof useLiveCallsStore.getState>["metrics"]>);
      }
    });

    operationsSocket.connect(getStoredToken() ?? undefined);

    return () => {
      unsubStatus();
      unsubMsg();
      operationsSocket.disconnect();
    };
  }, [setWsStatus, upsertCall, updateTranscript, setMetrics]);
}
