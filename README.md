# VOXERA

A real-time voice agent prototype: speech in, a spoken answer out, over one WebSocket.

```
microphone ──PCM16 20 ms frames──▶ speech-to-text ──▶ turn-taking ──▶ LLM (token stream)
                                                                        │ sentence by sentence
speaker   ◀──PCM16 20 ms frames── paced, interruptible ◀── text-to-speech ◀┘
```

It is a personal project by MD Zahid Hasan. It is not a product: there are no customers, no
certifications and no hosted service.

## What works

| Area | Status |
|---|---|
| Streaming pipeline over WebSocket (binary PCM16 in and out, JSON events) | Working, tested |
| Bounded inbound audio queue, drop-oldest under backpressure | Working, tested |
| Turn-taking state machine | Working, tested |
| Barge-in: user speech stops the reply while it is being generated **and while it is playing** | Working, tested |
| Sentence-by-sentence speech: TTS starts on the first finished sentence, not the full answer | Working, tested |
| Conversation history sent to the LLM (last `VOICE_HISTORY_TURNS` turns) | Working, tested |
| Provider adapters: Deepgram (STT); OpenAI, Anthropic, Groq, Azure OpenAI (LLM); ElevenLabs, OpenAI (TTS) | Implemented. **Not yet run against the live services in this revision** |
| Built-in mock engines for development (no keys needed) | Working. The mock recogniser invents words; the mock voice is a tone |
| Browser demo with live microphone and playback (`web/`) | Builds; text path checked in a browser. **Microphone path not yet tested by a person** |
| Phone calls through Twilio Media Streams (`app/telephony/`) | Implemented, unit-tested with fakes. **Never run against Twilio** |
| Latency benchmark (`scripts/bench_voice_latency.py`) | Working |

## Latency

Latency is measured from outside, the way a caller experiences it: recorded speech is played into
the WebSocket at microphone speed, and the clock runs from the last frame of speech to the first
frame of reply audio.

```bash
python scripts/bench_voice_latency.py --url ws://localhost:8000/api/v1/ --turns 20
python scripts/bench_voice_latency.py --barge-in --turns 12
```

**Results with the built-in mock engines** (29 October 2026, one laptop, client and server on the same
machine, 20 turns; 12 turns for barge-in):

| Measure | Median | 95th percentile |
|---|---|---|
| End of speech → first reply audio | 452 ms | 476 ms |
| Final transcript → first reply audio (server-side) | 149 ms | 168 ms |
| Final transcript → first LLM token (server-side) | 30 ms | 38 ms |
| Caller starts talking → reply stopped (barge-in) | 62 ms | 255 ms |

Read these as **pipeline overhead, not real-world latency**. The mock recogniser waits 300 ms of
silence before ending a turn (that is most of the first row), the mock LLM emits a token every
20–40 ms and the mock voice needs no network. Barge-in varies between runs (earlier medians 62–119 ms;
one slow turn in this run set the 95th percentile). The inbound queue no longer polls: the
dispatcher sleeps on an event and wakes as soon as a frame arrives.

**Results with real providers: not measured yet.** Add keys (below), run the same command, and put
the numbers here. Expect the end-of-speech figure to be dominated by the recogniser's end-of-turn
wait (`DEEPGRAM_ENDPOINTING_MS`, default 300), the LLM's time to first token and the TTS provider's
time to first audio.

The server also reports each turn to the client (`turn_metrics`) and exposes rolling percentiles at
`/api/v1/metrics` (`voxera_voice_first_audio_ms`).

## Run it

Requirements: Python 3.11, Node 18 or newer.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --port 8000
```

With no providers configured and `ENVIRONMENT=development`, the mock engines are used, so this works
without any API key.

Voice demo (live microphone, playback, latency readout), on http://localhost:5174:

```bash
cd web && npm install && npm run dev
```

`dashboard/` is the project's landing page and an admin console prototype. Its admin pages call
the agent-platform APIs, which now live on the `platform-sketches` branch (see below).

### Real providers

Set these in `.env`:

```
STT_PROVIDER=deepgram
DEEPGRAM_API_KEY=...
LLM_PROVIDER=groq            # or openai, anthropic, azure_openai
GROQ_API_KEY=...
TTS_PROVIDER=elevenlabs      # or openai_audio
ELEVENLABS_API_KEY=...
VOICE_TTS_VOICE_ID=...
```

Mock engines are never used when `ENVIRONMENT=production`; a missing provider is an error there.

## How the voice path works

- `app/api/v1/endpoints/websocket.py`: the transport. Binary frames go into a bounded queue
  (`app/streaming/`); JSON carries events. Protocol: [docs/voice-protocol.md](docs/voice-protocol.md).
- `app/voice/session.py`: one conversation. Owns turn-taking, the LLM stream, speech, history and
  per-turn timing, with no dependency on the transport, so it is tested without a network.
- `app/llm/llm_consumer.py` and `app/llm/sentence_chunker.py`: stream tokens and cut them into
  sentences as they arrive.
- `app/tts/tts_consumer.py`: speaks the sentences in order and paces audio to at most
  `VOICE_TTS_MAX_LEAD_MS` (250 ms) ahead of playback. Pacing is what makes barge-in effective:
  the client never holds seconds of speech that cannot be taken back.
- `app/conversation/`: the turn state machine. The system's turn lasts until its reply has been
  heard, so speech during playback counts as an interruption.
- `app/stt/`, `app/llm/providers/`, `app/tts/providers/`: engine interfaces and provider adapters,
  chosen by `app/voice/factory.py`.
- `app/telephony/`: the same consumers behind Twilio Media Streams (μ-law 8 kHz in and out).

## Known limits

- End of turn is a fixed silence wait. A pause in the middle of a sentence can end the turn early.
- Barge-in is detected from recognised speech, so it is as fast as the recogniser's first partial
  result. The browser demo relies on the browser's echo cancellation to keep the reply out of the mic.
- One LLM request per turn; no tool calling in the voice path.
- The audio queue assumes the client sends at real-time cadence, as a microphone does.

## Agent-platform sketches (moved to a branch)

Earlier revisions also carried design sketches of an "agent platform" (planner, verifier, workflow,
knowledge/RAG, memory, tools, integrations, tenants) with REST endpoints and unit tests. None of them
was used by the voice path, several were keyword rules or returned fixed sample data, and they had
no security review. They were removed from `main` to keep this repository focused on the voice
agent, and are kept unchanged on the
[`platform-sketches`](https://github.com/zahidhasancode/voxera/tree/platform-sketches) branch.

`app/iam` stays on `main`: it provides the token check used by the voice WebSocket in staging and
production.

## Tests

```bash
python -m pytest -m "not integration and not slow"     # 136 tests, no network, no database
ruff check app/ tests/ scripts/
```

The voice tests (`tests/voice/`, `tests/telephony_voice/`) use deterministic fake engines and cover
sentence streaming, interruption during generation and during playback, pacing, history, the
Deepgram end-of-turn logic, the 24 kHz → 16 kHz resampler and the WebSocket endpoint end to end.
`tests/streaming/` covers drop-oldest backpressure, event wake-up, frame order and clean shutdown of
the inbound audio path.

## Licence

MIT. See `LICENSE`.
