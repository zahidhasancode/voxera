# VOXERA — System Design

This document covers high-level system design, real-time constraints, latency budget, concurrency, async task lifecycle, backpressure, horizontal scaling, multi-tenancy, observability, security, and edge cases.

---

## 1. High-Level System Design

VOXERA is a **real-time voice AI pipeline** over a single WebSocket per session. The design goals:

- **Low perceived latency:** User speaks → system starts replying (audio) in under ~400ms where possible.
- **Interruptibility:** User can talk over the system; the system stops promptly and listens.
- **No blocking:** The WebSocket receive loop never waits on STT, LLM, or TTS. Ingress is enqueue-only; CPU and I/O run in async tasks.
- **Bounded resources:** Fixed-size queues, drop-oldest under load, no unbounded growth.

The system is a **pipeline of stages** with clear handoffs:

```
[Client] ←→ [WebSocket] ←→ [Queue] ←→ [Dispatcher] ←→ [STT] → [TurnManager] → [LLM] → [TTS] → [WebSocket] ←→ [Client]
```

Each stage is async. Blocking or slow downstream stages are isolated by queues and fire-and-forget dispatch so that the critical path (ingress and turn decisions) stays fast.

---

## 2. Real-Time Constraints

- **Frame cadence:** 20ms per PCM16 frame. The dispatcher ticks every 20ms; if work takes longer, the next tick is delayed but the queue does not grow without bound (drop-oldest at max size).
- **STT partials:** Target 50–100ms from speech to first partial. The mock meets this loosely; real STT (streaming APIs) must be tuned (chunk size, VAD) to stay in budget.
- **LLM time-to-first-token (TTFT):** Target &lt; 200ms. Mock is ~20–40ms per token; real LLM backends (vLLM, Triton, hosted APIs) drive this. Caching and small prompts help.
- **TTS time-to-first-audio (TTFA):** Target &lt; 100ms after `llm_final`. Mock and streaming TTS services can be tuned (streaming mode, chunk size) to stay in budget.
- **Barge-in response:** From user speech (partial) to LLM cancel and TTS stop: one turn of the event loop and task cancel. Typically &lt; 50ms in-process.

---

## 3. Latency Budget (Illustrative)

Rough end-to-end from **user stops speaking** to **first system audio**:

| Stage | Target (ms) | Notes |
|-------|-------------|-------|
| STT final after speech end | 50–150 | VAD + finalize; depends on STT. |
| TurnManager → LLM start | &lt; 5 | In-process, one callback. |
| LLM TTFT | 50–200 | Model and infra. |
| TTS TTFA | 50–100 | Streaming TTS. |
| Network (client ↔ server) | 20–80 | RTT, varies by region. |
| **Total (best case)** | **~200–400** | **Target “sub-400ms”.** |

Worst case (cold caches, network spike, overload) can be 1–2 seconds. Metrics (TTFT, TTFA, queue depth, drops) are used to detect and debug regressions.

---

## 4. Concurrency Model

- **Single-threaded event loop:** All app code runs in one asyncio event loop per process. No threading in the pipeline; no shared mutable state that needs locks across tasks.
- **Tasks:**
  - **Dispatcher loop:** One long-running task per connection; pulls from the queue every 20ms.
  - **STT `_process_loop`:** One task per `STTConsumer`; blocks on `queue.get()` for frames.
  - **STT `process_frame`:** Fire-and-forget `create_task`; does not block the dispatcher.
  - **LLM `_run`:** One task per generation; runs until stream ends or `CancelledError`.
  - **TTS `_run`:** One task per `start_speaking`; runs until stream ends or `CancelledError`.
- **Locks:** `AudioFrameQueue` uses `asyncio.Lock` around `enqueue`/`dequeue`. `StreamingMetrics` is designed for single-writer (pipeline) access; no explicit locks. `TTSConsumer` uses `asyncio.Lock` for `_buffer` and `_current_utterance_id` when starting/stopping.

---

## 5. Async Task Lifecycle

- **Connection up:**  
  - Create Queue, Dispatcher, STT, TurnManager, LLMConsumer, TTSConsumer.  
  - `stt_consumer.start()`, `dispatcher.start()`.  
  - Send `connection` + `status: connected`.

- **Connection down (disconnect, error):**  
  - `finally`: `llm_consumer.cancel()`, `await tts_consumer.stop()`, `await stt_consumer.stop()`, `await dispatcher.stop()`, `manager.disconnect(websocket)`.  
  - Order: stop producers (LLM, TTS), then STT, then dispatcher, so in-flight work drains or is cancelled before the queue is no longer consumed.

- **LLM:**  
  - `start_generation` cancels previous `_task` (if any), runs `on_system_turn_start`, then `create_task(_run)`.  
  - `_run` streams tokens, sends `llm_final` or `llm_cancelled`, and in `finally` runs `on_system_turn_end`.  
  - `cancel()` only does `task.cancel()`; the loop delivers `CancelledError` into `_run`.

- **TTS:**  
  - `start_speaking` cancels previous task, sets state, `create_task(_run)`.  
  - `_run` streams frames, and in `finally` sends `tts_metrics` and clears `_task` / `_current_utterance_id`.  
  - `stop()` cancels the task; `_run`’s `finally` still runs.

---

## 6. Backpressure Handling

- **AudioFrameQueue (50 frames):**  
  - If full, `enqueue` drops the oldest frame and appends the new one.  
  - `record_drop` in metrics; optional debug logging.  
  - Enqueue is non-blocking; the WebSocket `receive` loop never blocks on the queue.

- **StreamingDispatcher:**  
  - Does not block. If `dequeue` returns `None`, it sleeps for the remainder of the 20ms tick and continues. No backpressure to the client; we prefer drop-oldest over applying backpressure to the sender.

- **STTConsumer queue (50):**  
  - `process_frame` uses `put_nowait`; on `QueueFull` it drops and increments `frames_dropped`.  
  - The dispatcher does not wait on `process_frame`; it uses `create_task` so the dispatcher loop stays on cadence.

- **LLM / TTS:**  
  - No internal queues. They consume prompts/text and produce tokens/frames. If the client is slow to read, `send_json` / `send_bytes` can exert backpressure at the WebSocket buffer; that is outside the current design. For true backpressure, TTS could pause the engine when the send buffer is full; not implemented today.

---

## 7. Horizontal Scaling Strategy

- **Stateless app (per connection):** All session state lives in the WebSocket handler (queue, dispatcher, STT, TurnManager, LLM, TTS). No in-memory shared state between connections except `StreamingMetrics`.

- **Sticky sessions:** A given WebSocket must stay on the same process for its lifetime. Use load balancer affinity (cookie or header) based on the first request that upgrades to WebSocket. If the connection lands on a different process after reconnect, it is a new session.

- **Workers / instances:** Run multiple uvicorn workers or Kubernetes pods. Each has its own event loop and connections. `StreamingMetrics` is per-process; for global views, aggregate in a metrics backend (Prometheus, Datadog, etc.).

- **STT/LLM/TTS:**  
  - **In-process:** Scales with more app instances; each instance runs mock or in-process models.  
  - **Out-of-process:** STT/LLM/TTS as separate services (HTTP/gRPC). App uses async clients and timeouts. Same engine interfaces; swap implementations via config.

---

## 8. Multi-Tenant Considerations

- **Isolation:** Today, isolation is per-WebSocket: one queue, one STT/LLM/TTS flow per connection. Different connections do not share queues or engines.
- **Resource limits:** No per-tenant caps yet. Possible extensions: max concurrent connections per tenant, max queue depth, or rate limits on `dev_test_*` and LLM/TTS calls. These would live in a middleware or in the WebSocket handler before creating the pipeline.
- **Tenant context:** `conversation_id` (and optionally a `tenant_id` in config) can be passed into engines and logs for attribution and debugging. Not required for the core pipeline.

---

## 9. Observability and Metrics

- **StreamingMetrics:**  
  - `current_latency_ms`, `max_latency_ms`, `queue_depth`, `dropped_frames`.  
  - Exposed in `/api/v1/health` with `streaming_status` (OK / DEGRADED).  
  - Can be scraped or pushed to Prometheus/Datadog (integration not in repo).

- **LLM:**  
  - `time_to_first_token_ms`, `total_generation_ms`, `token_count`, `tokens_per_second` in `llm_final` and `llm_cancelled`.  
  - Can be aggregated in a metrics pipeline or logged for slow-request analysis.

- **TTS:**  
  - `time_to_first_audio_ms`, `total_audio_ms`, `frame_count`, `frames_per_second` in `tts_metrics`.  
  - Same: aggregate or log.

- **Logging:**  
  - Structured logs (`app.core.logger`) with `conversation_id`, `utterance_id`, and optionally `call_id` / `request_id`.  
  - Important events: connection up/down, user turn start/complete, barge-in, LLM complete/cancel, TTS start/stop.

- **Tracing:**  
  - No OpenTelemetry yet. `conversation_id` and `utterance_id` can be propagated to downstream services for distributed traces when STT/LLM/TTS are remote.

---

## 10. Security and Auth Strategy

- **Transport:** TLS in production; WebSocket over `wss://`. Termination at LB or reverse proxy is fine.

- **Auth:**  
  - Current: `ConnectionManager` accepts all connections (dev-friendly).  
  - Production: validate before `websocket.accept()`: API key, JWT, or OAuth token in header or query. Reject with 4xx and do not accept the WebSocket if invalid.

- **Origin / CORS:**  
  - CORS applies to HTTP. WebSocket does not use CORS; `Origin` can be checked in the upgrade handler if needed.  
  - Restrict `Origin` to known frontend hosts to reduce CSRF-style abuse.

- **Input:**  
  - Binary: trusted as PCM. If the source is untrusted, validate size (e.g. 640 bytes per frame) and rate.  
  - JSON: validate `type` and `text` length for `dev_test_transcript` and `dev_test_tts`. Reject or truncate oversized payloads.  
  - Disable or gate `dev_test_*` in production or behind a feature flag.

- **Secrets:**  
  - STT/LLM/TTS API keys in config or env; not in code or client. Use a secrets manager in production.

---

## 11. Edge Cases

- **Empty / very short user input:**  
  - STT may emit final with `transcript=""`. TurnManager still runs `UserTurnCompleted`. LLM and TTS will run with empty or short prompts; mock LLM yields a fixed phrase. Real LLMs may need special handling for empty input.

- **Rapid consecutive user turns:**  
  - Each `UserTurnCompleted` starts a new `start_generation`. `start_generation` cancels the previous `_task`. If the previous `_run` was still in its `on_system_turn_start` or token loop, it gets `CancelledError`, sends `llm_cancelled`, and runs `on_system_turn_end`. Only the latest generation continues. TTS for the previous turn is never started (we only start TTS from the latest `on_llm_final`).

- **Barge-in before first LLM token:**  
  - `UserTurnStarted` or `UserInterrupted` calls `llm_consumer.cancel()`. The LLM task is cancelled; `_run` sends `llm_cancelled` with whatever `accumulated_text` it has (possibly empty) and runs `on_system_turn_end`. TTS is not started for that turn.

- **Barge-in during TTS:**  
  - `UserInterrupted` or `on_user_turn_started` (via `_on_system_turn_start` when a new generation begins) calls `tts_consumer.stop()`. The TTS task is cancelled; `_run`’s `finally` still sends `tts_metrics`. Playback on the client should stop when the client sees barge-in or a new turn; the server does not send an explicit “stop playback” event.

- **WebSocket disconnect during LLM/TTS:**  
  - `send_json` / `send_bytes` may raise when the connection is closed. The `_run` tasks can hit these in `finally` or in the send loop. Catching and logging is recommended; the `finally` cleanup (e.g. `on_system_turn_end`) should still run where possible. The outer `finally` in the WebSocket handler still does `cancel`, `stop`, `disconnect`.

- **Clock / timestamp assumptions:**  
  - `StreamingMetrics` and engine metrics use `time.monotonic()` or `time.time()` and server-local clocks. For cross-service analysis, correlate with a shared timestamp or trace ID.

- **Very long utterances:**  
  - STT may emit many partials and one long final. LLM/TTS process the full transcript. For extremely long text, TTS and LLM could be chunked in future versions; currently they run over the full string. Timeouts on external STT/LLM/TTS calls are important.

- **No microphone / binary frames:**  
  - If the client never sends binary, the queue stays empty and the dispatcher mostly sleeps. STT receives nothing. `dev_test_transcript` and `dev_test_tts` still work for demos.
