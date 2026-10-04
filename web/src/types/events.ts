/** Backend WebSocket JSON event types */

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

/**
 * Provider names announced by the server, e.g. "mock", "deepgram", "openai".
 * null = the server did not name that provider.
 */
export interface Providers {
  stt: string | null;
  llm: string | null;
  tts: string | null;
}

export interface AudioFormat {
  sample_rate: number;
  frame_ms: number;
  encoding: string;
}

/**
 * Sent by the server once the session is ready. The client also raises a bare
 * `{type, status}` version of this event itself on socket open and close.
 */
export interface ConnectionEvent {
  type: "connection";
  status: string;
  conversation_id?: string;
  providers?: Partial<Record<keyof Providers, unknown>>;
  audio?: Partial<Record<keyof AudioFormat, unknown>>;
}

export interface PingEvent {
  type: "ping";
}

export interface PongEvent {
  type: "pong";
}

export interface LLMPartialEvent {
  type: "llm_partial";
  utterance_id: string;
  token: string;
  token_index: number;
  accumulated: string;
}

/** Any field the server leaves out or sends as a non-number is null, never 0. */
export interface LLMMetrics {
  time_to_first_token_ms: number | null;
  total_generation_ms: number | null;
  token_count: number | null;
  tokens_per_second: number | null;
}

export interface LLMFinalEvent {
  type: "llm_final";
  utterance_id: string;
  text: string;
  metrics?: unknown;
}

export interface LLMCancelledEvent {
  type: "llm_cancelled";
  utterance_id: string;
  partial_text: string;
  metrics?: unknown;
}

export interface TTSMetricsPayload {
  time_to_first_audio_ms: number | null;
  total_audio_ms: number | null;
  frame_count: number | null;
  frames_per_second: number | null;
}

export interface TTSMetricsEvent {
  type: "tts_metrics";
  utterance_id?: string;
  metrics?: unknown;
}

export interface TTSStartEvent {
  type: "tts_start";
  utterance_id: string;
}

export interface TTSEndEvent {
  type: "tts_end";
  utterance_id: string;
}

export interface TTSClearEvent {
  type: "tts_clear";
  utterance_id: string;
  reason?: string;
}

/** Server-side latencies for one turn. null = the server could not measure it. */
export interface TurnMetrics {
  utterance_id: string;
  transcript_final_to_llm_first_token_ms: number | null;
  transcript_final_to_first_audio_ms: number | null;
  llm_first_token_to_first_audio_ms: number | null;
}

export interface TurnMetricsEvent extends TurnMetrics {
  type: "turn_metrics";
}

export interface ServerErrorEvent {
  type: "error";
  code: string;
  message: string;
}

export interface TranscriptPartialEvent {
  type: "partial";
  utterance_id: string;
  transcript: string;
  confidence: number;
  timestamp: string;
}

export interface TranscriptFinalEvent {
  type: "final";
  utterance_id: string;
  transcript: string;
  confidence: number;
  timestamp: string;
}

export type BackendJsonEvent =
  | ConnectionEvent
  | PingEvent
  | PongEvent
  | LLMPartialEvent
  | LLMFinalEvent
  | LLMCancelledEvent
  | TTSMetricsEvent
  | TTSStartEvent
  | TTSEndEvent
  | TTSClearEvent
  | TurnMetricsEvent
  | ServerErrorEvent
  | TranscriptPartialEvent
  | TranscriptFinalEvent;

export function isBackendJsonEvent(obj: unknown): obj is BackendJsonEvent {
  return (
    typeof obj === "object" &&
    obj !== null &&
    typeof (obj as { type?: unknown }).type === "string"
  );
}

/** A finite number, or null. Used for every metric that arrives over the wire. */
export function numberOrNull(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}
