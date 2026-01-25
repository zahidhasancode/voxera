# VOXERA — Architecture

This document describes the backend architecture, streaming data flow, turn-taking and barge-in, LLM and TTS pipelines, cancellation, metrics, WebSocket message types, scaling, and fault tolerance.

---

## 1. Backend Architecture

### 1.1 Components

| Component | Role |
|-----------|------|
| **WebSocket endpoint** (`/api/v1/`) | Accepts connections, routes binary → `AudioFrameQueue`, JSON → `handle_message`. Creates per-connection: `ConversationState`, `TurnManager`, `LLMConsumer`, `TTSConsumer`, `AudioFrameQueue`, `StreamingDispatcher`, `STTConsumer`. |
| **AudioFrameQueue** | Bounded deque (default 50 frames). Non-blocking `enqueue`; when full, drop-oldest. `dequeue` used by `StreamingDispatcher`. |
| **StreamingDispatcher** | Loop every 20ms: `dequeue` → `frame_callback` (no-op today) and `STTConsumer.process_frame` (fire-and-forget). Keeps fixed cadence. |
| **STTConsumer** | Bounded queue of frames; `_process_loop` feeds `StreamingSTTEngine.process_audio`, `finalize_utterance`. Emits `TranscriptEvent` (partial/final) via `transcript_callback`. |
| **TurnManager** | Consumes `TranscriptEvent`. Updates `ConversationState`; emits `UserTurnStarted`, `UserTurnCompleted`, `UserInterrupted` to callbacks. |
| **LLMConsumer** | Driven by `on_user_turn_completed`. `start_generation` runs `engine.stream()`, sends `llm_partial`, `llm_final`, or `llm_cancelled`. `cancel()` on `UserTurnStarted` / `UserInterrupted`. |
| **TTSConsumer** | Driven by `on_llm_final(text, utterance_id)`. `engine.stream(text, utterance_id)` → `send_bytes` per PCM16 frame. Sends `tts_metrics` in `finally`. `stop()` on barge-in, system turn start, WebSocket cleanup. |
| **StreamingMetrics** | Singleton: enqueue/dequeue/dispatch timestamps, `current_latency_ms`, `max_latency_ms`, `queue_depth`, `dropped_frames`. Used by queue, dispatcher, and `/api/v1/health`. |

### 1.2 Layering

```
[WebSocket] → [Queue] → [Dispatcher] → [STT] ──┬─→ [TurnManager] → [LLM] → [TTS] → [WebSocket]
                ↑           │                    │
                └── Metrics ◄─────────────────────┘
```

- **Ingress:** WebSocket binary → Queue only. JSON goes to `handle_message` (ping, dev_test_*). No blocking.
- **Pipeline:** Queue → Dispatcher → STT. Dispatcher never blocks on STT (task is fire-and-forget).
- **Orchestration:** TurnManager is the only component that decides when to start LLM and when to cancel LLM/TTS.

---

## 2. Streaming Data Flow

### 2.1 Audio In

1. Client sends binary PCM16 (20ms, 16kHz, 640 bytes).
2. `websocket.receive()` yields `{"bytes": ...}`. `await audio_queue.enqueue(frame)` runs. If the queue is full, the oldest frame is evicted and `streaming_metrics.record_drop` is called; the new frame is always appended.
3. `StreamingDispatcher._dispatch_loop` runs every 20ms: `frame_with_id = await queue.dequeue()`. If a frame exists, it calls `frame_callback` and `asyncio.create_task(stt_consumer.process_frame(frame))`. Metrics: `record_dispatch(frame_id)`.

### 2.2 STT → Transcripts

1. `STTConsumer.process_frame(frame)` does `put_nowait(frame)`; if the queue is full, the frame is dropped and `frames_dropped` incremented.
2. `_process_loop` does `get()` on the queue, then `engine.process_audio(frame)` and optionally `engine.finalize_utterance()`. The engine returns `TranscriptEvent` or `None`.
3. For each `TranscriptEvent`, `transcript_callback` runs: `websocket.send_json(event.to_dict())` and `turn_manager.process_transcript_event(event)`.

### 2.3 TurnManager → LLM

1. **Partial + system speaking:** `handle_interruption()`: `complete_system_turn`, `UserInterrupted` → `on_user_interrupted` → `llm_consumer.cancel()`, `tts_consumer.stop()`.
2. **Partial + user not speaking:** `start_user_turn`, `UserTurnStarted` → `on_user_turn_started` → `llm_consumer.cancel()`.
3. **Final + user speaking:** `complete_user_turn`, `UserTurnCompleted` → `on_user_turn_completed` → `llm_consumer.start_generation(transcript, utterance_id, on_system_turn_start, on_system_turn_end, on_llm_final)`.

### 2.4 LLM → Tokens

1. `LLMConsumer.start_generation` cancels any existing `_task`, calls `on_system_turn_start` (which stops TTS and `start_system_turn`), then `asyncio.create_task(_run())`.
2. `_run` iterates `engine.stream(transcript, ...)`. For each `StreamToken`, it appends to `accumulated_text` and sends `llm_partial`. When the stream ends, it sends `llm_final` and calls `on_llm_final(full_text, utterance_id)`.
3. On `asyncio.CancelledError`, it sends `llm_cancelled` with `partial_text` and `metrics`. `finally` always runs `on_system_turn_end`.

### 2.5 TTS → Audio Out

1. `on_llm_final` calls `tts_consumer.start_speaking(text, utterance_id)`. `TTSConsumer` cancels any in-flight task and starts `_run(text, utterance_id)`.
2. `_run` does `async for frame in engine.stream(text, utterance_id=...)` and `await send_bytes(frame)`. On `CancelledError` it logs and exits. In `finally` it sends `tts_metrics` via `send_json` and clears `_task` / `_current_utterance_id`.
3. `tts_consumer.stop()` is used on: `on_system_turn_start`, `on_user_interrupted`, and in the WebSocket `finally` block. It cancels the task and clears the buffer.

---

## 3. Turn-Taking and Barge-In

### 3.1 ConversationState

- `is_user_speaking`, `is_system_speaking`, `turn_count`, `current_utterance_id`, `last_user_activity`.
- `start_user_turn`, `complete_user_turn`, `start_system_turn`, `complete_system_turn`, `interrupt_user`.

### 3.2 TurnManager Logic

| Event | Condition | Action |
|-------|-----------|--------|
| **Partial** | `is_system_speaking` | Barge-in: `handle_interruption` → `UserInterrupted` |
| **Partial** | `!is_user_speaking` | `start_user_turn`, `UserTurnStarted` |
| **Final** | `is_user_speaking` | `complete_user_turn`, `UserTurnCompleted` |

### 3.3 Barge-In Handling

- **UserInterrupted:** `on_user_interrupted` → `llm_consumer.cancel()`, `await tts_consumer.stop()`.
- **UserTurnStarted:** `on_user_turn_started` → `llm_consumer.cancel()` (TTS not yet started for this turn, or was already stopped by a previous `on_system_turn_start`).

---

## 4. LLM and TTS Streaming Pipelines

### 4.1 LLM

- **Interface:** `StreamingLLMEngine.stream(prompt, utterance_id=, conversation_id=) -> AsyncIterator[StreamToken]`, `last_metrics() -> LLMGenerationMetrics`.
- **Mock:** `MockStreamingLLMEngine` yields tokens with 20–40ms delay; on `CancelledError` it re-raises after updating `_last_metrics`.
- **Consumer:** Single `asyncio.Task` per generation. `cancel()` sets `task.cancel()`. Metrics (TTFT, total_ms, token_count, tokens/s) are sent with `llm_final` and `llm_cancelled`.

### 4.2 TTS

- **Interface:** `StreamingTTSEngine.stream(text, utterance_id=) -> AsyncIterator[bytes]`, `last_metrics() -> TTSAudioMetrics`.
- **Mock:** `MockStreamingTTSEngine` produces PCM16 20ms frames (silence/tone) per word with 15–30ms delay; supports cancellation.
- **Consumer:** Single task per `start_speaking`. `stop()` cancels the task. `tts_metrics` (TTFA, total_audio_ms, frame_count, frames/s) in `_run`’s `finally`.

---

## 5. Cancellation Model

- **LLM:** `LLMConsumer.cancel()` cancels `_task`. The coroutine in `_run` receives `CancelledError`, sends `llm_cancelled`, and runs `on_system_turn_end` in `finally`. The engine’s `stream()` must use `await asyncio.sleep(...)` (or similar) so the event loop can deliver the cancel.
- **TTS:** `TTSConsumer.stop()` cancels `_task`. `_run`’s `except CancelledError` and `finally` run; `tts_metrics` is still sent. `engine.stream()` must be cancellation-aware.
- **STT:** No explicit cancel from TurnManager. `STTConsumer.stop()` puts `None` in the queue and waits for the task; the engine’s `finalize_utterance` is called before that.
- **Dispatcher:** `stop()` sets `_running=False` and awaits the dispatch task with a short timeout, then cancels if needed. The loop exits when `_running` is false.

---

## 6. Metrics Collection

### 6.1 StreamingMetrics (Singleton)

- **record_enqueue(queue_depth, max_size):** `frame_id`, `queue_depth`, `_max_queue_depth`, `FrameMetrics(enqueue_time)`. Logs backpressure at 80% of `max_size`.
- **record_drop(queue_depth, max_size):** `dropped_frames += 1`.
- **record_dequeue(frame_id, queue_depth):** `dequeue_time`, `queue_depth`.
- **record_dispatch(frame_id):** `dispatch_time`, latency_ms → `current_latency_ms`, `max_latency_ms`, and rolling aggregates.

Used by: `AudioFrameQueue`, `StreamingDispatcher`. Exposed in `/api/v1/health` as `streaming_status` (OK if latency < 100ms and no drops, else DEGRADED), `current_latency_ms`, `max_latency_ms`, `dropped_frames`, `queue_depth`.

### 6.2 LLM and TTS Metrics

- **LLM:** `LLMGenerationMetrics`: `time_to_first_token_ms`, `total_generation_ms`, `token_count`, `tokens_per_second`. Sent in `llm_final` and `llm_cancelled`.
- **TTS:** `TTSAudioMetrics`: `time_to_first_audio_ms`, `total_audio_ms`, `frame_count`, `frames_per_second`. Sent in `tts_metrics` from `TTSConsumer._run`’s `finally`.

---

## 7. WebSocket Message Types

### 7.1 Server → Client (JSON)

| `type` | Main fields | When |
|--------|-------------|------|
| `connection` | `status`: `"connected"` | Right after `websocket.accept()` and pipeline init. |
| `ping` | — | Periodically when `receive()` times out (ping interval). |
| `partial` | `utterance_id`, `transcript`, `confidence`, `timestamp` | STT partial. |
| `final` | same | STT final. |
| `llm_partial` | `utterance_id`, `conversation_id`, `token`, `token_index`, `accumulated` | Each LLM token. |
| `llm_final` | `utterance_id`, `conversation_id`, `text`, `metrics` | LLM stream finished. |
| `llm_cancelled` | `utterance_id`, `conversation_id`, `partial_text`, `metrics` | LLM cancelled (barge-in or new user turn). |
| `tts_metrics` | `utterance_id`, `conversation_id`, `metrics` | After TTS stream completes or is cancelled. |

### 7.2 Server → Client (Binary)

- Raw PCM16 mono, 16kHz, 20ms per frame (640 bytes). Clients play via Web Audio API or similar.

### 7.3 Client → Server (JSON)

| `type` | Purpose |
|--------|---------|
| `ping` | Server responds `pong`. |
| `dev_test_transcript` | Inject final transcript; triggers TurnManager → LLM → TTS. |
| `dev_test_tts` | Inject TTS only; no TurnManager. |

### 7.4 Client → Server (Binary)

- PCM16 20ms frames. Enqueued into `AudioFrameQueue`.

---

## 8. Scalability

- **Single connection = one pipeline:** All components are per-WebSocket. No shared mutable state across connections except `StreamingMetrics` (singleton, used for pipeline observability).
- **Horizontal scaling:** Run multiple FastAPI/uvicorn workers or instances behind a load balancer. WebSocket stickiness (e.g., by `sec-websocket-key` or a route token) is required so a given client stays on one server for the lifetime of the call.
- **Vertical:** The main bottleneck is CPU for STT/LLM/TTS. Mock engines are cheap; real STT/LLM/TTS will dominate. Async I/O keeps the event loop free; CPU-bound work should be offloaded (process pool, external services, or GPUs).

---

## 9. Fault Tolerance

- **Queue full:** Drop-oldest; record in metrics and logs. Prevents unbounded memory and backpressure on the receive loop.
- **STT queue full:** `process_frame` drops and increments `frames_dropped`. No exception to the dispatcher.
- **LLM/TTS task errors:** `_run` uses `try/except CancelledError` and `finally`. On other exceptions, the task dies; `on_system_turn_end` is only guaranteed for the normal and `CancelledError` paths. Consider a broad `except` in `_run` to call `on_system_turn_end` and log.
- **WebSocket disconnect:** `WebSocketDisconnect` is caught; `finally` runs: `llm_consumer.cancel()`, `tts_consumer.stop()`, `stt_consumer.stop()`, `dispatcher.stop()`, `manager.disconnect(websocket)`.
- **Config:** `WEBSOCKET_PING_INTERVAL` / `WEBSOCKET_PING_TIMEOUT` help detect dead connections. Server sends `ping` on `receive` timeout; client should respond `pong` (handled in `handle_message` if the client sends `{"type":"pong"}`; server does not send `pong`, it sends `ping`).

---

## 10. Production Deployment Topology

- **App:** FastAPI behind ASGI server (uvicorn/gunicorn-uvicorn). TLS termination at load balancer or reverse proxy.
- **WebSocket:** Sticky sessions (cookies or custom headers) so a connection stays on one app instance. Proxy (e.g. Nginx, Envoy) must support WebSocket upgrade and long-lived connections.
- **STT/LLM/TTS:** Either in-process (same app) or out-of-process (HTTP/gRPC to separate services). For out-of-process, use `asyncio`-friendly clients and timeouts. Keep the same engine interfaces.
- **Observability:** Emit `streaming_status`, `current_latency_ms`, `dropped_frames`, `queue_depth` to a metrics backend. Use structured logs (`app.core.logger`) with `conversation_id`, `utterance_id`, `call_id` for tracing.
- **Secrets:** API keys for STT/LLM/TTS in config/env; never in code or client.
