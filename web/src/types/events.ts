/** Backend WebSocket JSON event types */

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export interface ConnectionEvent {
  type: "connection";
  status: string;
}

export interface PingEvent {
  type: "ping";
}

export interface LLMPartialEvent {
  type: "llm_partial";
  utterance_id: string;
  conversation_id: string;
  token: string;
  token_index: number;
  accumulated: string;
}

export interface LLMMetrics {
  time_to_first_token_ms: number;
  total_generation_ms: number;
  token_count: number;
  tokens_per_second: number;
}

export interface LLMFinalEvent {
  type: "llm_final";
  utterance_id: string;
  conversation_id: string;
  text: string;
  metrics: LLMMetrics;
}

export interface LLMCancelledEvent {
  type: "llm_cancelled";
  utterance_id: string;
  conversation_id: string;
  partial_text: string;
  metrics: LLMMetrics;
}

export interface TTSMetricsPayload {
  time_to_first_audio_ms: number;
  total_audio_ms: number;
  frame_count: number;
  frames_per_second: number;
}

export interface TTSMetricsEvent {
  type: "tts_metrics";
  utterance_id: string;
  conversation_id: string;
  metrics: TTSMetricsPayload;
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
  | LLMPartialEvent
  | LLMFinalEvent
  | LLMCancelledEvent
  | TTSMetricsEvent
  | TranscriptPartialEvent
  | TranscriptFinalEvent;

export function isBackendJsonEvent(obj: unknown): obj is BackendJsonEvent {
  return typeof obj === "object" && obj !== null && "type" in obj;
}
