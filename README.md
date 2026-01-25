# VOXERA

**Real-time voice AI platform** — streaming STT, LLM, and TTS over WebSockets with turn-taking, barge-in, and sub-400ms perceived latency.

---

## Project Overview

VOXERA solves the latency and rigidity of traditional voice assistants. Most systems wait for a full utterance, batch-process through STT → LLM → TTS, and only then play audio. That adds hundreds of milliseconds of delay and blocks natural interruptibility (barge-in).

VOXERA is built for **real-time conversational AI**:

- **Streaming end-to-end:** Audio in (PCM16) → STT (partial + final) → LLM (token stream) → TTS (PCM16 out) without waiting for completion at any stage.
- **Turn-taking and barge-in:** User can interrupt the system at any time; in-flight LLM and TTS are cancelled immediately and the system resumes listening.
- **Bounded, non-blocking pipelines:** Fixed-size queues, drop-oldest under backpressure, 20ms frame cadence, and structured metrics so the system never blocks the WebSocket receive loop.

The result is a platform suitable for **live demos, voice agents, and production deployments** where responsiveness and interruptibility matter.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Browser / App)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────────────────┐ │
│  │ Microphone   │  │ Web Audio    │  │ React UI: Conversation, Metrics,         │ │
│  │ → PCM16      │  │ API (PCM16   │  │ Turn State, Dev Controls                 │ │
│  │ 20ms frames  │  │ playback)    │  │                                          │ │
│  └──────┬───────┘  └──────▲───────┘  └─────────────────────────────────────────┘ │
│         │                 │                                                        │
│         └────────────────┼───────────────────────────────────────────────────────┤
│                          │         WebSocket (JSON + Binary)                       │
└──────────────────────────┼───────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────────────────────┐
│                     VOXERA BACKEND (FastAPI)                                       │
│                          │                                                         │
│  ┌──────────────────────▼──────────────────────┐                                  │
│  │           WebSocket Endpoint (/api/v1/)       │                                  │
│  │  • Binary: enqueue → AudioFrameQueue          │                                  │
│  │  • JSON: dev_test_transcript, dev_test_tts,    │                                  │
│  │    ping/pong                                   │                                  │
│  └──────────────────────┬──────────────────────┘                                  │
│                         │                                                          │
│  ┌──────────────────────▼──────────────────────┐     ┌─────────────────────────┐ │
│  │     AudioFrameQueue (bounded, 50 frames)      │     │   StreamingMetrics      │ │
│  │     • Drop-oldest when full                   │────▶│   latency, queue_depth,  │ │
│  │     • Non-blocking enqueue                    │     │   dropped_frames         │ │
│  └──────────────────────┬──────────────────────┘     └─────────────────────────┘ │
│                         │                                                          │
│  ┌──────────────────────▼──────────────────────┐                                  │
│  │     StreamingDispatcher (20ms cadence)        │                                  │
│  │     • dequeue → frame_callback                │                                  │
│  │     • fan-out → STTConsumer (process_frame)   │                                  │
│  └──────────────────────┬──────────────────────┘                                  │
│                         │                                                          │
│           ┌─────────────┼─────────────┐                                            │
│           ▼             ▼             ▼                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                                    │
│  │ STT Engine  │ │ TurnManager │ │ (future:     │                                    │
│  │ (MockSTT)   │ │             │ │  recorder,  │                                    │
│  │ partial/    │ │ Conversation│ │  VAD, etc.) │                                    │
│  │ final       │ │ State       │ └─────────────┘                                    │
│  └──────┬──────┘ └──────┬──────┘                                                    │
│         │               │                                                            │
│         │     UserTurnCompleted ──▶ LLMConsumer ──▶ llm_partial / llm_final /          │
│         │                            │            llm_cancelled                      │
│         │                            │                                                  │
│         │     UserTurnStarted ──▶ cancel LLM                                            │
│         │     UserInterrupted ──▶ cancel LLM + TTS                                       │
│         │                            │                                                  │
│         │                            ▼                                                  │
│         │                    TTSConsumer ◀── llm_final (text + utterance_id)           │
│         │                     • MockStreamingTTSEngine                                  │
│         │                     • stream() → send_bytes(PCM16)                            │
│         │                     • tts_metrics on done/cancel                               │
│         │                                                                               │
│  transcript_callback ──▶ WebSocket (partial/final) + TurnManager.process_transcript    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|--------|-------------|
| **Streaming STT** | Partial transcripts every ~50–100ms; final on silence. Pluggable engine (mock today). |
| **Streaming LLM** | Token-by-token generation with TTFT, tokens/s, total ms. Cancellable on barge-in. |
| **Streaming TTS** | PCM16 mono 16kHz, 20ms frames. Starts on `llm_final`; stops on user interrupt. |
| **Turn-taking** | `TurnManager` + `ConversationState`: user turn start/complete, system turn start/end. |
| **Barge-in** | User speech during system response → `UserInterrupted` → cancel LLM + TTS, resume listening. |
| **Bounded pipeline** | 50-frame audio queue, drop-oldest; 20ms dispatcher cadence; no unbounded growth. |
| **Metrics** | `StreamingMetrics` (latency, queue depth, drops); LLM/TTS metrics over WebSocket; `/api/v1/health`. |
| **Dev controls** | `dev_test_transcript` (fake final → LLM→TTS), `dev_test_tts` (TTS only) for demos without a mic. |

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.11, FastAPI, uvicorn, WebSockets, Pydantic, pydantic-settings |
| **Frontend** | Vite, React 18, TypeScript, TailwindCSS, Recharts, Web Audio API |
| **Transport** | Native WebSocket (no Socket.IO); JSON (events) + binary (PCM16) |
| **Audio** | PCM16 mono, 16kHz, 20ms frames (640 bytes) |

---

## Repo Structure

```
VOXERA/
├── app/                          # FastAPI backend
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── health.py         # /api/v1/health (streaming metrics)
│   │   │   └── websocket.py      # WebSocket /api/v1/
│   │   └── router.py
│   ├── conversation/            # Turn-taking core
│   │   ├── state.py              # ConversationState (user/system turn, turn_count)
│   │   ├── turn_manager.py       # process_transcript_event → UserTurn* / UserInterrupted
│   │   └── events.py             # UserTurnStarted, UserTurnCompleted, UserInterrupted
│   ├── core/                     # Config, logger, connection manager, middleware
│   ├── llm/                      # Streaming LLM
│   │   ├── streaming_engine.py   # StreamingLLMEngine (ABC), MockStreamingLLMEngine
│   │   └── llm_consumer.py       # start_generation, cancel; llm_partial/final/cancelled
│   ├── stt/                      # Streaming STT
│   │   ├── engine.py             # StreamingSTTEngine (ABC), MockSTTEngine
│   │   ├── consumer.py           # STTConsumer (queue, process_loop, transcript_callback)
│   │   └── models.py             # TranscriptEvent, TranscriptType
│   ├── tts/                      # Streaming TTS
│   │   ├── streaming_engine.py   # StreamingTTSEngine (ABC), MockStreamingTTSEngine
│   │   └── tts_consumer.py       # start_speaking, stop; send_bytes + tts_metrics
│   ├── streaming/                # Audio pipeline
│   │   ├── audio_queue.py        # AudioFrameQueue (bounded, drop-oldest)
│   │   ├── dispatcher.py         # StreamingDispatcher (20ms cadence, STT fan-out)
│   │   └── metrics.py            # StreamingMetrics (singleton), FrameMetrics
│   ├── main.py
│   └── ...
├── web/                          # Vite + React frontend
│   ├── src/
│   │   ├── websocket/            # VoxeraWebSocket client
│   │   ├── audio/                # PCM16Player (Web Audio API)
│   │   ├── store/                # VoxeraContext (turns, metrics, connection)
│   │   ├── components/           # Header, Conversation, Audio, TurnState, Metrics, DevControls
│   │   └── types/                # Backend JSON event types
│   └── ...
├── docs/                         # Architecture, system design, product, demo
├── tests/
├── requirements.txt
├── pyproject.toml
└── docker-compose.yml
```

---

## Local Development

### Prerequisites

- **Python 3.11+**
- **Node 18+**
- Backend and frontend run on different ports; WebSocket and HTTP are proxied in dev.

### Backend

```bash
cd VOXERA
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # optional: adjust CORS, SECRET_KEY, etc.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs` (when `ENVIRONMENT=development`)
- Health: `http://localhost:8000/api/v1/health`

### Frontend

```bash
cd VOXERA/web
npm install
npm run dev
```

- App: `http://localhost:5173`
- Vite proxies `/api` → `http://localhost:8000`, so `ws://localhost:5173/api/v1/` reaches the backend WebSocket.

Override WebSocket URL:

```bash
VITE_WS_URL=ws://localhost:8000/api/v1/ npm run dev
```

---

## How Real-Time Streaming Works

1. **Ingress:** Client sends binary PCM16 (20ms) or JSON. Binary frames are enqueued into `AudioFrameQueue` without blocking. If the queue is full, the oldest frame is dropped.

2. **Dispatcher:** `StreamingDispatcher` runs a loop every 20ms: dequeue one frame, pass to `frame_callback`, and fan out to `STTConsumer.process_frame` via a fire-and-forget task so the dispatcher never waits on STT.

3. **STT:** `STTConsumer` pushes frames into `MockSTTEngine` (or a real engine). The engine emits `TranscriptEvent` (partial or final). Each event is sent to the client as JSON and to `TurnManager.process_transcript_event`.

4. **Turn-taking:** On **partial** while `is_system_speaking` → barge-in: `UserInterrupted` → cancel LLM and TTS. On **partial** with `!is_user_speaking` → `UserTurnStarted` → cancel any in-flight LLM. On **final** with `is_user_speaking` → `UserTurnCompleted` → start LLM generation.

5. **LLM:** `LLMConsumer.start_generation` runs `engine.stream()`, sends `llm_partial` per token, then `llm_final` (or `llm_cancelled` on `CancelledError`). On `llm_final`, `_on_llm_final` calls `tts_consumer.start_speaking(text, utterance_id)`.

6. **TTS:** `TTSConsumer` runs `engine.stream(text, utterance_id)`, sends each PCM16 frame via `send_bytes`. On completion or cancel, it sends `tts_metrics`. `tts_consumer.stop()` is called on barge-in, system turn start, and WebSocket cleanup.

7. **Egress:** Client receives JSON events and binary PCM16. The React app uses `PCM16Player` (Web Audio API) for playback and `VoxeraContext` for turns, metrics, and connection state.

---

## WebSocket Protocol Overview

**Endpoint:** `ws://localhost:8000/api/v1/` (or `wss://` in production).

### Client → Server

| Type | Format | Purpose |
|------|--------|---------|
| **Binary** | Raw PCM16 mono, 16kHz, 20ms (640 bytes) | Live microphone audio |
| `ping` | `{"type":"ping"}` | Keepalive (server replies `pong`) |
| `dev_test_transcript` | `{"type":"dev_test_transcript","text":"..."}` | Inject final transcript → LLM → TTS (no mic) |
| `dev_test_tts` | `{"type":"dev_test_tts","text":"..."}` | Inject TTS-only (no LLM) |

### Server → Client

| Type | Description |
|------|-------------|
| `connection` | `{"type":"connection","status":"connected"}` on connect |
| `ping` | Server sends periodically; client should `pong` |
| `partial` | STT partial: `utterance_id`, `transcript`, `confidence`, `timestamp` |
| `final` | STT final: same fields |
| `llm_partial` | `utterance_id`, `conversation_id`, `token`, `token_index`, `accumulated` |
| `llm_final` | `utterance_id`, `conversation_id`, `text`, `metrics` (TTFT, total_ms, token_count, tokens/s) |
| `llm_cancelled` | `utterance_id`, `conversation_id`, `partial_text`, `metrics` |
| `tts_metrics` | `utterance_id`, `conversation_id`, `metrics` (TTFA, total_audio_ms, frame_count, frames/s) |
| **Binary** | Raw PCM16 20ms frames for playback |

See `web/src/types/events.ts` and `app/llm/llm_consumer.py`, `app/tts/tts_consumer.py`, `app/stt/models.py` for exact schemas.

---

## Why This Architecture

- **Single WebSocket per session:** Keeps all state (queue, dispatcher, STT, turn manager, LLM, TTS) in one connection. No cross-server coordination for a single call.
- **Bounded queues and drop-oldest:** Prevents unbounded memory and ensures we don’t pile up latency when downstream is slow. Drop-oldest favors freshness over completeness for real-time feel.
- **20ms cadence:** Matches typical voice (20ms) frames; keeps processing regular and predictable.
- **Abstract engines:** `StreamingSTTEngine`, `StreamingLLMEngine`, `StreamingTTSEngine` allow swapping mocks for OpenAI, vLLM, Triton, cloud TTS, etc., without changing the pipeline.
- **Turn manager as the single source of truth:** All LLM and TTS starts/stops go through `TurnManager` callbacks. Barge-in and turn boundaries are explicit and testable.
- **Cancellation via asyncio:** LLM and TTS use `asyncio.create_task` and `task.cancel()`. Engines use `await asyncio.sleep(...)` so `CancelledError` is raised and `finally` runs for metrics and cleanup.

---

## Extending with Real STT / LLM / TTS

- **STT:** Implement `StreamingSTTEngine`: `async def process_audio(self, frame: bytes) -> Optional[TranscriptEvent]`, `async def finalize_utterance(self) -> Optional[TranscriptEvent]`. Wire to Deepgram, AssemblyAI, Whisper, or similar; keep the same `TranscriptEvent` and `TranscriptType`.
- **LLM:** Implement `StreamingLLMEngine`: `async def stream(self, prompt, *, utterance_id, conversation_id) -> AsyncIterator[StreamToken]`, `last_metrics() -> LLMGenerationMetrics`. Compatible with OpenAI Realtime, vLLM, Triton, or any async token API.
- **TTS:** Implement `StreamingTTSEngine`: `async def stream(self, text, *, utterance_id) -> AsyncIterator[bytes]` (PCM16 20ms), `last_metrics() -> TTSAudioMetrics`. Swap in ElevenLabs, PlayHT, or local models.

Replace the mock in `app/api/v1/endpoints/websocket.py` (and, if needed, add config for provider/API keys). The rest of the pipeline remains unchanged.

---

## Screenshots

| Screenshot | Description |
|------------|-------------|
| *[Conversation + Metrics dashboard]* | Main demo UI: conversation, turn state, LLM/TTS metrics, dev controls. |
| *[Health / streaming status]* | `/api/v1/health` with `streaming_status`, `current_latency_ms`, `dropped_frames`, `queue_depth`. |

*(Add actual screenshots under `docs/images/` and link here.)*

---

## Demo Instructions

1. Start backend: `uvicorn app.main:app --reload --port 8000`
2. Start frontend: `cd web && npm run dev`
3. Open `http://localhost:5173`, click **Connect**
4. **Without microphone:**
   - `dev_test_transcript`: enter e.g. `What can you help me with?` → **Send**. Expect: partial/final transcript, `llm_partial`/`llm_final`, TTS audio and `tts_metrics`.
   - `dev_test_tts`: enter text → **TTS**. Expect: PCM16 playback and `tts_metrics`.
5. **With microphone:** Send binary PCM16 (20ms, 16kHz). Expect STT partial/final, then LLM and TTS. To test barge-in, speak again while the system is responding; LLM and TTS should cancel and you should see `llm_cancelled` and an “Interrupted” state in the UI.

See **docs/demo.md** for a live demo script and investor-friendly talking points.

---

## Why This Demonstrates Senior-Level Engineering

- **Async streaming end-to-end:** No blocking in the receive loop; queues, dispatcher, STT, LLM, and TTS are fully async with clear task ownership and cancellation.
- **Cancellation safety:** LLM and TTS handle `CancelledError`, send `llm_cancelled`/`tts_metrics` in `finally`, and `tts_consumer.stop()` is invoked on barge-in and disconnect. No orphaned tasks or leaked resources.
- **Real-time turn management:** `TurnManager` and `ConversationState` encode clear state transitions (user/system, start/complete, interrupt). Behavior is deterministic and unit-testable.
- **Metrics-driven design:** `StreamingMetrics` from enqueue to dispatch; LLM and TTS metrics on every completion or cancel; health endpoint exposes streaming health. Enables SLOs and operational debugging.
- **Clean abstractions:** Engine interfaces (`StreamingSTTEngine`, `StreamingLLMEngine`, `StreamingTTSEngine`) separate pipeline from providers. Consumers (STT, LLM, TTS) only depend on these interfaces and WebSocket send primitives.

---

## License and Contributions

- **License:** Proprietary — VOXERA.  
- **Contributions:** Internal only unless otherwise agreed. For external contributions, open an issue to discuss scope and licensing.

---

## Further Reading

- [docs/architecture.md](docs/architecture.md) — Backend design, data flow, cancellation, WebSocket message types, scaling.
- [docs/system-design.md](docs/system-design.md) — Latency budget, concurrency, backpressure, scaling, observability.
- [docs/product-overview.md](docs/product-overview.md) — Non-technical overview for investors and founders.
- [docs/demo.md](docs/demo.md) — Demo script, talking points, and Q&A.
