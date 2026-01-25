import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { VoxeraWebSocket } from "@/websocket";
import { PCM16Player } from "@/audio";
import type {
  BackendJsonEvent,
  LLMPartialEvent,
  LLMFinalEvent,
  LLMCancelledEvent,
  TTSMetricsEvent,
  TranscriptPartialEvent,
  TranscriptFinalEvent,
  LLMMetrics,
  TTSMetricsPayload,
  ConnectionStatus,
} from "@/types/events";

export interface Turn {
  id: string;
  role: "user" | "system";
  text: string;
  isPartial?: boolean;
  cancelled?: boolean;
  utteranceId?: string;
  timestamp: number;
}

export interface VoxeraState {
  connectionStatus: ConnectionStatus;
  turns: Turn[];
  systemSpeaking: boolean;
  userSpeaking: boolean;
  bargeIn: boolean;
  lastLlmMetrics: LLMMetrics | null;
  lastTtsMetrics: TTSMetricsPayload | null;
  audioFrameCount: number;
  audioActive: boolean;
  llmMetricHistory: LLMMetrics[];
  ttsMetricHistory: TTSMetricsPayload[];
}

const defaultMetrics: LLMMetrics = {
  time_to_first_token_ms: 0,
  total_generation_ms: 0,
  token_count: 0,
  tokens_per_second: 0,
};

const defaultTtsMetrics: TTSMetricsPayload = {
  time_to_first_audio_ms: 0,
  total_audio_ms: 0,
  frame_count: 0,
  frames_per_second: 0,
};

const defaultState: VoxeraState = {
  connectionStatus: "disconnected",
  turns: [],
  systemSpeaking: false,
  userSpeaking: false,
  bargeIn: false,
  lastLlmMetrics: null,
  lastTtsMetrics: null,
  audioFrameCount: 0,
  audioActive: false,
  llmMetricHistory: [],
  ttsMetricHistory: [],
};

type VoxeraContextValue = VoxeraState & {
  connect: () => void;
  disconnect: () => void;
  sendJson: (obj: object) => void;
  sendDevTestTranscript: (text: string) => void;
  sendDevTestTts: (text: string) => void;
  clearConversation: () => void;
};

const VoxeraContext = createContext<VoxeraContextValue | null>(null);

const MAX_METRIC_HISTORY = 30;

export function VoxeraProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<VoxeraState>(defaultState);
  const wsRef = useRef<VoxeraWebSocket | null>(null);
  const playerRef = useRef<PCM16Player | null>(null);
  const bargeInTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const systemTurnByUtteranceRef = useRef<Map<string, number>>(new Map()); // utterance_id -> turn index

  const connect = useCallback(() => {
    if (wsRef.current?.connected) return;
    setState((s) => ({ ...s, connectionStatus: "connecting" }));

    const player = new PCM16Player({
      onStateChange: (playing) => {
        setState((s) => ({ ...s, audioActive: playing === "playing" }));
      },
      onFramePlayed: (n) => {
        setState((s) => ({ ...s, audioFrameCount: n }));
      },
    });
    player.init();
    playerRef.current = player;

    const ws = new VoxeraWebSocket(
      (data: unknown) => {
        const ev = data as BackendJsonEvent;
        if (!ev || typeof ev !== "object" || !("type" in ev)) return;

        switch (ev.type) {
          case "connection":
            setState((s) => ({
              ...s,
              connectionStatus: (ev as { status: string }).status === "connected" ? "connected" : "disconnected",
            }));
            break;

          case "ping":
            ws.sendJson({ type: "pong" });
            break;

          case "llm_partial": {
            const e = ev as LLMPartialEvent;
            setState((s) => {
              const map = new Map(systemTurnByUtteranceRef.current);
              let idx = map.get(e.utterance_id);
              const turns = [...s.turns];
              if (idx == null) {
                idx = turns.length;
                map.set(e.utterance_id, idx);
                turns.push({
                  id: `sys-${e.utterance_id}`,
                  role: "system",
                  text: e.accumulated,
                  isPartial: true,
                  utteranceId: e.utterance_id,
                  timestamp: Date.now(),
                });
              } else {
                turns[idx] = { ...turns[idx], text: e.accumulated, isPartial: true };
              }
              systemTurnByUtteranceRef.current = map;
              return {
                ...s,
                turns,
                systemSpeaking: true,
              };
            });
            break;
          }

          case "llm_final": {
            const e = ev as LLMFinalEvent;
            setState((s) => {
              const idx = systemTurnByUtteranceRef.current.get(e.utterance_id);
              const turns = [...s.turns];
              if (idx != null && turns[idx]) {
                turns[idx] = { ...turns[idx], text: e.text, isPartial: false, cancelled: false };
              } else {
                turns.push({
                  id: `sys-${e.utterance_id}`,
                  role: "system",
                  text: e.text,
                  isPartial: false,
                  utteranceId: e.utterance_id,
                  timestamp: Date.now(),
                });
              }
              systemTurnByUtteranceRef.current = new Map();
              const hist = [...s.llmMetricHistory, e.metrics].slice(-MAX_METRIC_HISTORY);
              return {
                ...s,
                turns,
                systemSpeaking: s.audioActive,
                lastLlmMetrics: e.metrics,
                llmMetricHistory: hist,
              };
            });
            break;
          }

          case "llm_cancelled": {
            const e = ev as LLMCancelledEvent;
            setState((s) => {
              const idx = systemTurnByUtteranceRef.current.get(e.utterance_id);
              const turns = [...s.turns];
              if (idx != null && turns[idx]) {
                turns[idx] = { ...turns[idx], text: e.partial_text, isPartial: false, cancelled: true };
              } else {
                turns.push({
                  id: `sys-${e.utterance_id}`,
                  role: "system",
                  text: e.partial_text,
                  isPartial: false,
                  cancelled: true,
                  utteranceId: e.utterance_id,
                  timestamp: Date.now(),
                });
              }
              systemTurnByUtteranceRef.current = new Map();
              const hist = [...s.llmMetricHistory, e.metrics].slice(-MAX_METRIC_HISTORY);
              if (bargeInTimeoutRef.current) clearTimeout(bargeInTimeoutRef.current);
              bargeInTimeoutRef.current = setTimeout(() => {
                setState((prev) => ({ ...prev, bargeIn: false }));
              }, 3000);
              return {
                ...s,
                turns,
                systemSpeaking: s.audioActive,
                bargeIn: true,
                lastLlmMetrics: e.metrics,
                llmMetricHistory: hist,
              };
            });
            break;
          }

          case "tts_metrics": {
            const e = ev as TTSMetricsEvent;
            setState((s) => {
              const hist = [...s.ttsMetricHistory, e.metrics].slice(-MAX_METRIC_HISTORY);
              return {
                ...s,
                lastTtsMetrics: e.metrics,
                ttsMetricHistory: hist,
              };
            });
            break;
          }

          case "partial": {
            const e = ev as TranscriptPartialEvent;
            setState((s) => ({ ...s, userSpeaking: true }));
            break;
          }

          case "final": {
            const e = ev as TranscriptFinalEvent;
            setState((s) => {
              const turns = [...s.turns, {
                id: `usr-${e.utterance_id}`,
                role: "user" as const,
                text: e.transcript,
                timestamp: Date.now(),
              }];
              return { ...s, turns, userSpeaking: false };
            });
            break;
          }

          default:
            break;
        }
      },
      (buf: ArrayBuffer) => {
        playerRef.current?.push(buf);
      }
    );

    wsRef.current = ws;
    ws.connect();
  }, []);

  const disconnect = useCallback(() => {
    if (bargeInTimeoutRef.current) {
      clearTimeout(bargeInTimeoutRef.current);
      bargeInTimeoutRef.current = null;
    }
    wsRef.current?.disconnect();
    wsRef.current = null;
    playerRef.current?.close();
    playerRef.current = null;
    systemTurnByUtteranceRef.current = new Map();
    setState(defaultState);
  }, []);

  const sendJson = useCallback((obj: object) => {
    wsRef.current?.sendJson(obj);
  }, []);

  const sendDevTestTranscript = useCallback((text: string) => {
    setState((s) => ({
      ...s,
      turns: [
        ...s.turns,
        { id: `usr-${Date.now()}`, role: "user", text, timestamp: Date.now() },
      ],
    }));
    wsRef.current?.sendJson({ type: "dev_test_transcript", text });
  }, []);

  const sendDevTestTts = useCallback((text: string) => {
    wsRef.current?.sendJson({ type: "dev_test_tts", text });
  }, []);

  const clearConversation = useCallback(() => {
    systemTurnByUtteranceRef.current = new Map();
    setState((s) => ({
      ...s,
      turns: [],
      lastLlmMetrics: null,
      lastTtsMetrics: null,
      llmMetricHistory: [],
      ttsMetricHistory: [],
      audioFrameCount: 0,
    }));
    playerRef.current?.reset();
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const value: VoxeraContextValue = useMemo(
    () => ({
      ...state,
      connect,
      disconnect,
      sendJson,
      sendDevTestTranscript,
      sendDevTestTts,
      clearConversation,
    }),
    [state, connect, disconnect, sendJson, sendDevTestTranscript, sendDevTestTts, clearConversation]
  );

  return <VoxeraContext.Provider value={value}>{children}</VoxeraContext.Provider>;
}

export function useVoxera(): VoxeraContextValue {
  const ctx = useContext(VoxeraContext);
  if (!ctx) throw new Error("useVoxera must be used within VoxeraProvider");
  return ctx;
}
