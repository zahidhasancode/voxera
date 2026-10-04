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
import { ENCODING, FRAME_MS, MicCapture, PCM16Player, SAMPLE_RATE } from "@/audio";
import {
  isBackendJsonEvent,
  numberOrNull,
  type ConnectionEvent,
  type LLMPartialEvent,
  type LLMFinalEvent,
  type LLMCancelledEvent,
  type TTSMetricsEvent,
  type TTSClearEvent,
  type TurnMetricsEvent,
  type ServerErrorEvent,
  type TranscriptPartialEvent,
  type TranscriptFinalEvent,
  type LLMMetrics,
  type TTSMetricsPayload,
  type TurnMetrics,
  type Providers,
  type ConnectionStatus,
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

export type MicStatus = "off" | "starting" | "on";

/** Measured in this browser: final transcript received → first reply audio played. */
export interface ClientLatency {
  utteranceId: string;
  finalToFirstAudioMs: number;
}

export interface ServerError {
  code: string;
  message: string;
}

export interface VoxeraState {
  connectionStatus: ConnectionStatus;
  conversationId: string | null;
  /** null until the server announces them. */
  providers: Providers | null;
  /** Set when the server announces an audio format this client does not speak. */
  audioFormatError: string | null;
  turns: Turn[];
  /** Reply audio is playing (or scheduled to play) in this browser. */
  systemSpeaking: boolean;
  userSpeaking: boolean;
  bargeIn: boolean;
  micStatus: MicStatus;
  micError: string | null;
  /** RMS of recent microphone frames, 0..1. */
  micLevel: number;
  lastLlmMetrics: LLMMetrics | null;
  lastTtsMetrics: TTSMetricsPayload | null;
  lastTurnMetrics: TurnMetrics | null;
  clientLatency: ClientLatency | null;
  audioFrameCount: number;
  audioActive: boolean;
  llmMetricHistory: LLMMetrics[];
  ttsMetricHistory: TTSMetricsPayload[];
  connectionError: string | null;
  serverError: ServerError | null;
}

const defaultState: VoxeraState = {
  connectionStatus: "disconnected",
  conversationId: null,
  providers: null,
  audioFormatError: null,
  turns: [],
  systemSpeaking: false,
  userSpeaking: false,
  bargeIn: false,
  micStatus: "off",
  micError: null,
  micLevel: 0,
  lastLlmMetrics: null,
  lastTtsMetrics: null,
  lastTurnMetrics: null,
  clientLatency: null,
  audioFrameCount: 0,
  audioActive: false,
  llmMetricHistory: [],
  ttsMetricHistory: [],
  connectionError: null,
  serverError: null,
};

type VoxeraContextValue = VoxeraState & {
  connect: () => void;
  disconnect: () => void;
  startMic: () => Promise<void>;
  stopMic: () => void;
  sendJson: (obj: object) => void;
  sendDevTestTranscript: (text: string) => void;
  sendDevTestTts: (text: string) => void;
  clearConversation: () => void;
  dismissServerError: () => void;
};

const VoxeraContext = createContext<VoxeraContextValue | null>(null);

const MAX_METRIC_HISTORY = 30;
const BARGE_IN_BADGE_MS = 3000;
/** Mic level reaches the UI once per this many 20 ms frames. */
const MIC_LEVEL_EVERY_FRAMES = 5;

function stringOrNull(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

function toLlmMetrics(raw: unknown): LLMMetrics | null {
  if (!raw || typeof raw !== "object") return null;
  const m = raw as Record<string, unknown>;
  return {
    time_to_first_token_ms: numberOrNull(m.time_to_first_token_ms),
    total_generation_ms: numberOrNull(m.total_generation_ms),
    token_count: numberOrNull(m.token_count),
    tokens_per_second: numberOrNull(m.tokens_per_second),
  };
}

function toTtsMetrics(raw: unknown): TTSMetricsPayload | null {
  if (!raw || typeof raw !== "object") return null;
  const m = raw as Record<string, unknown>;
  const metrics: TTSMetricsPayload = {
    time_to_first_audio_ms: numberOrNull(m.time_to_first_audio_ms),
    total_audio_ms: numberOrNull(m.total_audio_ms),
    frame_count: numberOrNull(m.frame_count),
    frames_per_second: numberOrNull(m.frames_per_second),
  };
  return Object.values(metrics).some((v) => v !== null) ? metrics : null;
}

/** Describe a server audio format this client cannot handle, or null if it matches. */
function audioFormatMismatch(audio: ConnectionEvent["audio"]): string | null {
  if (!audio) return null;
  const { sample_rate, frame_ms, encoding } = audio;
  const ok =
    (sample_rate === undefined || sample_rate === SAMPLE_RATE) &&
    (frame_ms === undefined || frame_ms === FRAME_MS) &&
    (encoding === undefined || encoding === ENCODING);
  if (ok) return null;
  return (
    `The server announced ${String(encoding)} at ${String(sample_rate)} Hz in ${String(frame_ms)} ms frames; ` +
    `this client sends and plays ${ENCODING} at ${SAMPLE_RATE} Hz in ${FRAME_MS} ms frames.`
  );
}

/** Insert or update the assistant turn for one utterance. */
function upsertSystemTurn(turns: Turn[], utteranceId: string, patch: Partial<Turn>): Turn[] {
  const id = `sys-${utteranceId}`;
  const idx = turns.findIndex((t) => t.id === id);
  const next = [...turns];
  if (idx >= 0) {
    next[idx] = { ...next[idx], ...patch };
  } else {
    next.push({ id, role: "system", text: "", utteranceId, timestamp: Date.now(), ...patch });
  }
  return next;
}

export function VoxeraProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<VoxeraState>(defaultState);
  const wsRef = useRef<VoxeraWebSocket | null>(null);
  const playerRef = useRef<PCM16Player | null>(null);
  const micRef = useRef<MicCapture | null>(null);
  const bargeInTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  /** After tts_clear, audio still in flight is dropped until the next tts_start. */
  const dropAudioRef = useRef(false);
  /** Latest final transcript not yet followed by a tts_start. */
  const lastFinalRef = useRef<{ at: number; utteranceId: string } | null>(null);
  /** The final transcript whose reply audio is awaited, for the client latency readout. */
  const awaitedFinalRef = useRef<{ at: number; utteranceId: string } | null>(null);

  const stopMic = useCallback(() => {
    const mic = micRef.current;
    micRef.current = null;
    void mic?.stop();
    setState((s) =>
      s.micStatus === "off" && s.micLevel === 0 ? s : { ...s, micStatus: "off", micLevel: 0 }
    );
  }, []);

  const startMic = useCallback(async () => {
    if (!wsRef.current?.connected || micRef.current) return;

    let framesSinceLevel = 0;
    let peakRms = 0;
    const mic = new MicCapture({
      onFrame: (pcm) => {
        wsRef.current?.sendBinary(pcm);
      },
      onLevel: (rms) => {
        peakRms = Math.max(peakRms, rms);
        if (++framesSinceLevel < MIC_LEVEL_EVERY_FRAMES) return;
        const level = peakRms;
        framesSinceLevel = 0;
        peakRms = 0;
        setState((s) => (s.micLevel === level ? s : { ...s, micLevel: level }));
      },
      onEnded: (reason) => {
        if (micRef.current !== mic) return;
        micRef.current = null;
        setState((s) => ({ ...s, micStatus: "off", micLevel: 0, micError: reason }));
      },
    });
    micRef.current = mic;
    setState((s) => ({ ...s, micStatus: "starting", micError: null }));

    try {
      await mic.start();
      // Turned off, or the session ended, while the permission prompt was open.
      if (micRef.current !== mic) return;
      setState((s) => ({ ...s, micStatus: "on" }));
    } catch (err) {
      if (micRef.current !== mic) return;
      micRef.current = null;
      setState((s) => ({
        ...s,
        micStatus: "off",
        micLevel: 0,
        micError: err instanceof Error ? err.message : String(err),
      }));
    }
  }, []);

  const flagBargeIn = useCallback(() => {
    if (bargeInTimeoutRef.current) clearTimeout(bargeInTimeoutRef.current);
    bargeInTimeoutRef.current = setTimeout(() => {
      bargeInTimeoutRef.current = null;
      setState((s) => ({ ...s, bargeIn: false }));
    }, BARGE_IN_BADGE_MS);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current) return;
    setState((s) => ({ ...s, connectionStatus: "connecting", connectionError: null }));

    const player = new PCM16Player({
      onStateChange: (playback) => {
        const playing = playback === "playing";
        setState((s) => ({
          ...s,
          audioActive: playing,
          systemSpeaking: playing,
          audioFrameCount: player.frameCount,
        }));
      },
      onFirstAudio: (heardAtMs) => {
        const awaited = awaitedFinalRef.current;
        if (!awaited) return;
        awaitedFinalRef.current = null;
        setState((s) => ({
          ...s,
          clientLatency: {
            utteranceId: awaited.utteranceId,
            finalToFirstAudioMs: heardAtMs - awaited.at,
          },
        }));
      },
    });
    // Called from the Connect click, so the AudioContext is allowed to start.
    player.init().catch(() => undefined);
    playerRef.current = player;
    dropAudioRef.current = false;
    lastFinalRef.current = null;
    awaitedFinalRef.current = null;

    const ws = new VoxeraWebSocket(
      (data: unknown) => {
        if (!isBackendJsonEvent(data)) return;
        const ev = data;

        switch (ev.type) {
          case "connection": {
            const e = ev as ConnectionEvent;
            if (e.status !== "connected") {
              // Socket closed (or never opened): end the session's audio as well.
              wsRef.current = null;
              playerRef.current = null;
              void player.close();
              stopMic();
              setState((s) => ({
                ...s,
                connectionStatus: "disconnected",
                conversationId: null,
                providers: null,
                audioFormatError: null,
                userSpeaking: false,
                connectionError:
                  s.connectionStatus === "connecting"
                    ? "Could not connect to server"
                    : s.connectionError,
              }));
              break;
            }
            const providers: Providers | null = e.providers
              ? {
                  stt: stringOrNull(e.providers.stt),
                  llm: stringOrNull(e.providers.llm),
                  tts: stringOrNull(e.providers.tts),
                }
              : null;
            const conversationId = stringOrNull(e.conversation_id);
            const formatError = audioFormatMismatch(e.audio);
            setState((s) => ({
              ...s,
              connectionStatus: "connected",
              connectionError: null,
              conversationId: conversationId ?? s.conversationId,
              providers: providers ?? s.providers,
              audioFormatError: e.audio ? formatError : s.audioFormatError,
            }));
            break;
          }

          // A server ping needs no reply, and this client sends none of its own.
          case "ping":
          case "pong":
            break;

          case "llm_partial": {
            const e = ev as LLMPartialEvent;
            setState((s) => ({
              ...s,
              turns: upsertSystemTurn(s.turns, e.utterance_id, {
                text: e.accumulated,
                isPartial: true,
              }),
            }));
            break;
          }

          case "llm_final": {
            const e = ev as LLMFinalEvent;
            const metrics = toLlmMetrics(e.metrics);
            setState((s) => ({
              ...s,
              turns: upsertSystemTurn(s.turns, e.utterance_id, {
                text: e.text,
                isPartial: false,
                cancelled: false,
              }),
              lastLlmMetrics: metrics ?? s.lastLlmMetrics,
              llmMetricHistory: metrics
                ? [...s.llmMetricHistory, metrics].slice(-MAX_METRIC_HISTORY)
                : s.llmMetricHistory,
            }));
            break;
          }

          case "llm_cancelled": {
            const e = ev as LLMCancelledEvent;
            const metrics = toLlmMetrics(e.metrics);
            flagBargeIn();
            setState((s) => ({
              ...s,
              turns: upsertSystemTurn(s.turns, e.utterance_id, {
                text: e.partial_text,
                isPartial: false,
                cancelled: true,
              }),
              bargeIn: true,
              lastLlmMetrics: metrics ?? s.lastLlmMetrics,
              llmMetricHistory: metrics
                ? [...s.llmMetricHistory, metrics].slice(-MAX_METRIC_HISTORY)
                : s.llmMetricHistory,
            }));
            break;
          }

          case "tts_start": {
            dropAudioRef.current = false;
            if (lastFinalRef.current) {
              awaitedFinalRef.current = lastFinalRef.current;
              lastFinalRef.current = null;
            }
            player.beginStream();
            break;
          }

          // Audio already queued keeps playing; the player reports idle when it drains.
          case "tts_end":
            break;

          case "tts_clear": {
            const e = ev as TTSClearEvent;
            dropAudioRef.current = true;
            awaitedFinalRef.current = null;
            player.clear();
            if (e.reason === "barge_in") {
              flagBargeIn();
              setState((s) => ({ ...s, bargeIn: true }));
            }
            break;
          }

          case "tts_metrics": {
            const e = ev as TTSMetricsEvent;
            const metrics = toTtsMetrics(e.metrics ?? e);
            if (!metrics) break;
            setState((s) => ({
              ...s,
              lastTtsMetrics: metrics,
              ttsMetricHistory: [...s.ttsMetricHistory, metrics].slice(-MAX_METRIC_HISTORY),
            }));
            break;
          }

          case "turn_metrics": {
            const e = ev as TurnMetricsEvent;
            const metrics: TurnMetrics = {
              utterance_id: e.utterance_id,
              transcript_final_to_llm_first_token_ms: numberOrNull(
                e.transcript_final_to_llm_first_token_ms
              ),
              transcript_final_to_first_audio_ms: numberOrNull(
                e.transcript_final_to_first_audio_ms
              ),
              llm_first_token_to_first_audio_ms: numberOrNull(
                e.llm_first_token_to_first_audio_ms
              ),
            };
            setState((s) => ({ ...s, lastTurnMetrics: metrics }));
            break;
          }

          case "error": {
            const e = ev as ServerErrorEvent;
            setState((s) => ({
              ...s,
              serverError: {
                code: stringOrNull(e.code) ?? "unknown",
                message: stringOrNull(e.message) ?? "The server reported an error without a message.",
              },
            }));
            break;
          }

          case "partial": {
            const e = ev as TranscriptPartialEvent;
            if (typeof e.transcript !== "string" || !e.transcript.trim()) break;
            setState((s) => {
              const partialId = `usr-partial-${e.utterance_id ?? "live"}`;
              const idx = s.turns.findIndex((t) => t.id === partialId);
              const turns = [...s.turns];
              if (idx >= 0) {
                turns[idx] = { ...turns[idx], text: e.transcript, isPartial: true };
              } else {
                turns.push({
                  id: partialId,
                  role: "user",
                  text: e.transcript,
                  isPartial: true,
                  timestamp: Date.now(),
                });
              }
              return { ...s, turns, userSpeaking: true };
            });
            break;
          }

          case "final": {
            const e = ev as TranscriptFinalEvent;
            const text = typeof e.transcript === "string" ? e.transcript : "";
            if (text.trim()) {
              lastFinalRef.current = { at: performance.now(), utteranceId: e.utterance_id };
            }
            setState((s) => {
              const turns = [...s.turns];
              // The final replaces this utterance's live partial bubble, if there is one.
              let idx = turns.findIndex((t) => t.id === `usr-partial-${e.utterance_id}`);
              if (idx < 0) {
                idx = turns.findIndex((t) => t.role === "user" && t.isPartial);
              }
              if (!text.trim()) {
                if (idx >= 0) turns.splice(idx, 1);
                return { ...s, turns, userSpeaking: false };
              }
              let id = `usr-${e.utterance_id}`;
              if (turns.some((t) => t.id === id)) id = `${id}-${turns.length}`;
              const turn: Turn = {
                id,
                role: "user",
                text,
                isPartial: false,
                utteranceId: e.utterance_id,
                timestamp: idx >= 0 ? turns[idx].timestamp : Date.now(),
              };
              if (idx >= 0) turns[idx] = turn;
              else turns.push(turn);
              return { ...s, turns, userSpeaking: false };
            });
            break;
          }

          // Unknown message types are ignored.
          default:
            break;
        }
      },
      (buf: ArrayBuffer) => {
        if (dropAudioRef.current) return;
        player.push(buf);
      }
    );

    wsRef.current = ws;
    ws.connect();
  }, [stopMic, flagBargeIn]);

  const disconnect = useCallback(() => {
    if (bargeInTimeoutRef.current) {
      clearTimeout(bargeInTimeoutRef.current);
      bargeInTimeoutRef.current = null;
    }
    const mic = micRef.current;
    micRef.current = null;
    void mic?.stop();
    wsRef.current?.disconnect();
    wsRef.current = null;
    // close() stops every scheduled source and drops queued audio first.
    void playerRef.current?.close();
    playerRef.current = null;
    lastFinalRef.current = null;
    awaitedFinalRef.current = null;
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
    setState((s) => ({
      ...s,
      turns: [],
      lastLlmMetrics: null,
      lastTtsMetrics: null,
      lastTurnMetrics: null,
      clientLatency: null,
      llmMetricHistory: [],
      ttsMetricHistory: [],
      audioFrameCount: 0,
    }));
    playerRef.current?.reset();
  }, []);

  const dismissServerError = useCallback(() => {
    setState((s) => ({ ...s, serverError: null }));
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
      startMic,
      stopMic,
      sendJson,
      sendDevTestTranscript,
      sendDevTestTts,
      clearConversation,
      dismissServerError,
    }),
    [
      state,
      connect,
      disconnect,
      startMic,
      stopMic,
      sendJson,
      sendDevTestTranscript,
      sendDevTestTts,
      clearConversation,
      dismissServerError,
    ]
  );

  return <VoxeraContext.Provider value={value}>{children}</VoxeraContext.Provider>;
}

export function useVoxera(): VoxeraContextValue {
  const ctx = useContext(VoxeraContext);
  if (!ctx) throw new Error("useVoxera must be used within VoxeraProvider");
  return ctx;
}
