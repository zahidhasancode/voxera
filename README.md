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
| End of turn reads the words: a sentence that ends on "and", "for", "um" or a comma waits up to 700 ms for the caller to go on | Working, tested. Not yet measured with real callers |
| Sentence-by-sentence speech: TTS starts on the first finished sentence, not the full answer | Working, tested |
| Conversation history sent to the LLM (last `VOICE_HISTORY_TURNS` turns) | Working, tested |
| Provider adapters: Deepgram, Amazon Transcribe (STT); OpenAI, Anthropic, Groq, xAI, Azure OpenAI, Amazon Bedrock (LLM); ElevenLabs, OpenAI, Amazon Polly (TTS) | Deepgram, Amazon Transcribe and Amazon Polly **measured against the live services** (results below). Amazon Bedrock implemented and unit-tested; the live run is waiting for AWS account verification. The others are implemented, not yet run live |
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

**Results with real providers** (laptop on home Wi-Fi in Barcelona, server on the same laptop;
raw results in [`benchmarks/`](benchmarks/)). The language model is still the mock in these runs,
so the "first reply audio" rows do not yet include a real LLM's time to first token.

| Measure (median / 95th percentile) | Deepgram STT (29 Oct) | Amazon Transcribe + Amazon Polly (30 Oct, eu-west-1) |
|---|---|---|
| End of speech → final transcript | **634 / 702 ms** | **711 / 761 ms** |
| End of speech → first reply audio | 786 / 862 ms (mock voice) | **943 / 1102 ms** (real Polly voice) |
| Final transcript → first reply audio (server-side) | 152 / 170 ms (mock voice) | 228 / 306 ms (Polly) |
| Caller starts talking → reply stopped, barge-in from the recogniser's first words | 445 / 472 ms | 731 / 759 ms |
| **Caller starts talking → reply stopped, barge-in from raw audio (VAD, 30 Oct)** | **63 / 109 ms** | not re-measured |
| Audio frames received after the stop signal | 0 | 0 |

20 turns each; 12 turns for barge-in. What the numbers show:

- About 300 ms of "end of speech → final transcript" is the deliberate end-of-turn silence wait;
  the rest is recognition plus the network round trip from Barcelona.
- Barge-in used to wait for the recogniser's first partial result, so it followed the
  recogniser (Deepgram about 0.3 s faster than Transcribe). Voxera now also watches the raw
  inbound audio (`app/voice/vad.py`): three consecutive 20 ms frames clearly louder than the learned
  background stop the reply. That cut barge-in from 445 ms to 63 ms (median) with Deepgram, with
  no audio sent after the stop and no false interruptions in 20 normal turns.
- Polly adds roughly 200 ms from the first finished sentence to the first audio frame.

Not measured yet: a real LLM in the loop (Amazon Bedrock is waiting for account verification) and
ElevenLabs.

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
LLM_PROVIDER=groq            # or openai, anthropic, azure_openai, xai, bedrock
GROQ_API_KEY=...
TTS_PROVIDER=elevenlabs      # or openai_audio, amazon_polly
ELEVENLABS_API_KEY=...
VOICE_TTS_VOICE_ID=...
```

All-AWS setup (no API keys; credentials come from the standard AWS chain, e.g. `AWS_PROFILE`):

```
STT_PROVIDER=amazon_transcribe
LLM_PROVIDER=bedrock
TTS_PROVIDER=amazon_polly
AWS_VOICE_REGION=eu-west-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
POLLY_VOICE_ID=Joanna
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

- End of turn is a silence wait plus a word check (`app/voice/end_of_turn.py`): a transcript that
  ends on a joining word, an article, a filler or a comma waits up to `VOICE_EOT_HOLD_MS` (700 ms)
  for the caller to go on. It is an English word list, not a model, and cannot hear intonation; a
  pause after a complete-sounding phrase ("I'd like the pasta... and a salad") still ends the turn.
- Fast barge-in (`VOICE_VAD_BARGE_IN`, on by default) reacts to loudness, not words: a cough or a
  loud noise also stops the reply. It relies on the client's echo cancellation (browsers provide it)
  to keep the agent's own voice out of the microphone, so the phone bridge does not use it.
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
python -m pytest -m "not integration and not slow"     # 174 tests, no network, no database
ruff check app/ tests/ scripts/
```

The voice tests (`tests/voice/`, `tests/telephony_voice/`) use deterministic fake engines and cover
sentence streaming, interruption during generation and during playback, pacing, history, the
Deepgram end-of-turn logic, the 24 kHz → 16 kHz resampler and the WebSocket endpoint end to end.
`tests/streaming/` covers drop-oldest backpressure, event wake-up, frame order and clean shutdown of
the inbound audio path.

## Licence

MIT. See `LICENSE`.
