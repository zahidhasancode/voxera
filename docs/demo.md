# VOXERA — Demo Guide

Live demo script, investor-focused talking points, what to show technically, how to explain streaming and barge-in, and common Q&A.

---

## 1. Live Demo Script

### Setup (5 min)

1. **Backend:**  
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

2. **Frontend:**  
   `cd web && npm run dev`  
   Open `http://localhost:5173`.

3. **Connect:**  
   Click **Connect** in the header. Confirm “Connected” and a green status.

4. **Optional:**  
   `curl -s http://localhost:8000/api/v1/health` to show `streaming_status`, `queue_depth`, `dropped_frames`.

---

### Act 1: Full Loop Without a Microphone (2–3 min)

**Say:**  
“First, I’ll show the full pipeline without a mic—everything is triggered from the UI.”

1. In **Developer Controls**, use **Test transcript (→ LLM → TTS)**:
   - Text: `What can you help me with?`
   - Click **Send**.

2. **Point out:**
   - **Conversation:** User bubble appears, then a system bubble. Tokens stream in (partial text and cursor) until the final message.
   - **Turn-Taking:** State goes User → System → Idle.
   - **Audio:** “Playing” and frame count increase while TTS runs.
   - **Metrics:** LLM (TTFT, tokens/s, total ms) and TTS (TTFA, frames/s, frame count) update.
   - **Final:** “You said: …” style reply and TTS playing it.

**Say:**  
“That’s STT-equivalent input → LLM → TTS in one shot. The UI is getting partial tokens over the wire and playing audio as it’s streamed.”

---

### Act 2: TTS-Only (1 min)

**Say:**  
“We can also drive TTS directly for audio-only demos.”

1. In **Test TTS only**:
   - Text: `This is a streaming TTS test.`
   - Click **TTS**.

2. **Point out:**
   - Audio plays; **Audio Playback** shows “Playing” and frame count.
   - **Metrics** for TTS: TTFA, total_audio_ms, frames/s.
   - `tts_metrics` is sent when the stream ends.

**Say:**  
“TTS is the same engine we use after the LLM—same format, same metrics. This is just bypassing the LLM for a quick audio check.”

---

### Act 3: Barge-In (With Mic or dev_test) (2 min)

**Option A — With microphone:**  
“When I speak, STT sends partials. If I start talking while the system is replying, we get a barge-in.”

1. Send a transcript (e.g. `Tell me a short story`) and wait for the system to start speaking.
2. **While it’s speaking**, say something clearly (e.g. “Stop” or “Wait”).
3. **Point out:**
   - **Turn-Taking:** “Barge-in” or “User interrupted.”
   - **Conversation:** The last system bubble can show “Interrupted” (if the UI supports it from `llm_cancelled`).
   - **Audio:** Stops quickly.
   - **Metrics:** `llm_cancelled` with `partial_text` and metrics.

**Option B — Without microphone (dev_test only):**  
“We can simulate barge-in by sending a new `dev_test_transcript` while the system is still replying.”

1. Send: `Tell me something long.`
2. As soon as you see tokens streaming, send another: `Never mind.`
3. **Point out:**  
   The first LLM (and its TTS) is cancelled; the second takes over. “That’s the same cancellation path we use when you talk over the system with a real mic.”

---

### Act 4: Metrics and Health (1–2 min)

1. **Health:**  
   `GET /api/v1/health`  
   - `streaming_status`: OK or DEGRADED (based on latency and drops).
   - `current_latency_ms`, `max_latency_ms`, `dropped_frames`, `queue_depth`.

2. **In the UI:**  
   - LLM: TTFT, total ms, tokens/s.  
   - TTS: TTFA, total ms, frames/s, frame count.  
   - Latency badges (e.g. green &lt;200ms, yellow &lt;500ms, red ≥500ms) if the UI implements them.

**Say:**  
“We measure at every stage. In production we’d set SLOs on TTFT and TTFA and alert on queue depth and drops.”

---

### Closing (1 min)

**Say:**  
“So: streaming STT, LLM, and TTS; explicit turn-taking; barge-in with immediate cancel of LLM and TTS; and metrics end-to-end. The same design works with real STT, LLM, and TTS—we’re using mocks here for a reliable demo.”

---

## 2. What to Say to Investors

- **Problem:**  
  “Most voice AI is batch-based: you talk, wait, then get a reply. It feels slow and you can’t interrupt. That’s a product and UX ceiling.”

- **Approach:**  
  “VOXERA streams everything: speech-to-text, LLM, and text-to-speech. You see and hear the response as it’s generated, and you can interrupt at any time. We’ve built the pipeline and turn-taking so that behavior is reliable, not best-effort.”

- **Differentiation:**  
  “We’re not just wrapping an LLM in an API. We’re solving latency and interruptibility in the architecture: bounded queues, drop-oldest under load, cancellation from the turn manager. That’s what makes it feel like a conversation instead of a form.”

- **Traction / stage:**  
  “We have a working end-to-end platform with a React frontend and FastAPI backend. We’re on mocks for STT/LLM/TTS today; the next step is plugging in real providers and running pilots in [e.g. contact center, internal tools].”

- **Ask:**  
  “We’re raising [X] to [hire / integrate providers / run pilots]. I’d like to walk you through a quick demo and then discuss [partnership / pilot / investment].”

---

## 3. What to Show Technically

- **Architecture (high level):**  
  One WebSocket per session; binary for audio, JSON for events. Pipeline: Queue → Dispatcher → STT → TurnManager → LLM → TTS. Each stage is async; TurnManager is the single place that decides when to start or cancel LLM and TTS.

- **Streaming:**  
  - STT: partial and final events.  
  - LLM: `llm_partial` (token + accumulated), `llm_final`, `llm_cancelled`.  
  - TTS: raw PCM16 over the same WebSocket; `tts_metrics` when done or cancelled.  
  - “We never wait for the full response before starting the next stage.”

- **Barge-in:**  
  - User speech (partial) while `is_system_speaking` → `UserInterrupted` → `llm_consumer.cancel()`, `tts_consumer.stop()`.  
  - “The TurnManager is the only place that triggers cancel. That keeps behavior consistent and testable.”

- **Backpressure and bounds:**  
  - Fixed-size audio queue (e.g. 50 frames), drop-oldest when full.  
  - Dispatcher runs at 20ms; it doesn’t block on STT.  
  - “We’d rather drop old audio than buffer unbounded or block the receive loop.”

- **Metrics:**  
  - Pipeline: enqueue → dequeue → dispatch; `StreamingMetrics` for latency and drops.  
  - LLM: TTFT, total_generation_ms, tokens/s.  
  - TTS: TTFA, total_audio_ms, frames/s.  
  - “We can set SLOs and debug regressions with this.”

---

## 4. How to Explain Streaming and Barge-In

### Streaming

- **Without streaming:**  
  “You finish speaking → we send the whole utterance to STT → wait for final transcript → send to LLM → wait for full reply → send to TTS → play. That’s several round-trips of latency.”

- **With streaming:**  
  “We send small audio chunks (e.g. 20ms) as you talk. STT gives us partials every 50–100ms and a final when you stop. As soon as we have a final, we start the LLM and stream tokens. We don’t wait for the last token—we send each one to TTS and play audio as it’s ready. You hear the start of the reply much sooner.”

- **In the demo:**  
  “Watch the system bubble: the text appears in chunks. That’s `llm_partial` over the WebSocket. The audio is the same idea: we play 20ms frames as we get them from TTS.”

### Barge-In

- **Without barge-in:**  
  “If you talk while the system is speaking, either your speech is ignored, or it’s queued and played after. Both feel wrong.”

- **With barge-in:**  
  “As soon as we get a partial transcript while the system is in a ‘speaking’ turn, we treat it as an interruption. We cancel the in-flight LLM and TTS and switch back to listening. The user’s new input becomes the next turn.”

- **In the demo:**  
  “When I talk over the system, you’ll see the audio stop and the turn state show ‘User interrupted’ or ‘Barge-in.’ Behind the scenes we’re cancelling the LLM and TTS tasks and sending `llm_cancelled` and `tts_metrics` so the client and our metrics stay consistent.”

---

## 5. Common Questions and Answers

**Q: Why not use [OpenAI Realtime / another full-stack API]?**  
A: “We want a pipeline we control: swap STT, LLM, and TTS independently; run on-prem or in a VPC; and enforce our own latency and turn-taking. Realtime-style APIs are one option we can plug in as an LLM, but we don’t want to be locked to a single provider or deployment model.”

**Q: How do you hit sub-400ms?**  
A: “By streaming at every stage and not waiting for completion. The budget is roughly: STT final ~50–150ms, LLM TTFT ~50–200ms, TTS TTFA ~50–100ms, plus network. We tune each engine and measure with TTFT, TTFA, and pipeline latency. The mocks are optimistic; real providers need to be chosen and configured to stay in budget.”

**Q: What if the user talks over the system constantly?**  
A: “Each new user partial during a system turn triggers a cancel. We don’t try to merge or reorder; we treat it as a new turn. If it becomes noisy, we could add a short debounce or VAD, but the core behavior is: user speech wins, system stops.”

**Q: How does this scale?**  
A: “Each WebSocket is independent: its own queue, dispatcher, STT, TurnManager, LLM, TTS. We scale by adding app instances and using sticky sessions so a connection stays on one instance. STT/LLM/TTS can be in-process or out-of-process; we use the same interfaces.”

**Q: Is it multi-tenant?**  
A: “Right now isolation is per-connection. We can add tenant or account id, rate limits, and quotas later. The design doesn’t assume shared state between connections.”

**Q: What about [language X] / [accent / noisy environment]?**  
A: “That’s mostly in the STT and, to some extent, the LLM. Our job is to pass through audio and transcripts and to maintain low latency and turn-taking. We’d pick or train STT for the target languages and conditions; the rest of the pipeline is language-agnostic.”

**Q: How do you handle disconnects and failures?**  
A: “On disconnect we cancel LLM, stop TTS, stop STT, stop the dispatcher, and remove the connection. We use `finally` blocks so we always clean up. For external STT/LLM/TTS, we’d use timeouts and retries; the pipeline stays the same.”

**Q: Can I run this on-prem?**  
A: “Yes. The app is a normal FastAPI service. You can run it in your own network, point it at your own STT/LLM/TTS (or ours in a private deployment), and keep all traffic on your side. We’re happy to discuss on-prem or VPC deployment.”

---

## 6. Demo Checklist

- [ ] Backend and frontend start without errors.  
- [ ] Connect shows “Connected” and health shows `streaming_status`.  
- [ ] `dev_test_transcript` produces user + system bubbles, streaming tokens, audio, and LLM/TTS metrics.  
- [ ] `dev_test_tts` produces TTS audio and `tts_metrics`.  
- [ ] Barge-in (mic or second `dev_test_transcript`) shows cancel, “Interrupted”/“Barge-in,” and audio stopping.  
- [ ] `/api/v1/health` returns `streaming_status`, `current_latency_ms`, `dropped_frames`, `queue_depth`.  
- [ ] Clear conversation works.  
- [ ] No console or server errors during the demo.

---

## 7. If Something Goes Wrong

- **“Connected” never appears:**  
  Check backend is on 8000 (or the port the frontend proxies to). Check browser console for WebSocket errors. If using `VITE_WS_URL`, ensure it matches the backend.

- **No tokens or audio after Send:**  
  Check server logs for errors in LLM or TTS. Ensure `TurnManager` and `on_user_turn_completed` are being triggered (final transcript). For TTS-only, ensure `dev_test_tts` and `tts_consumer.start_speaking` are being called.

- **Barge-in doesn’t stop audio:**  
  Barge-in requires a **partial** while the system is speaking. With only `dev_test_transcript`, you need to send a second `dev_test_transcript` while the first LLM is still streaming. With a mic, ensure the mike is active and STT is emitting partials.

- **Metrics are zero or stale:**  
  `StreamingMetrics` is updated when audio flows through the queue and dispatcher. If you never send binary frames, pipeline metrics stay at zero. LLM/TTS metrics only update after a completed or cancelled generation. For health, send some traffic first.

- **CORS or 403 on WebSocket:**  
  Check `CORS_ORIGINS` and `ConnectionManager`. In dev, the default often allows `localhost`. For production, add your frontend origin explicitly.
