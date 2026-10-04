# Voice Infrastructure Architecture

VOXERA's live voice stack runs over WebSocket (`/api/v1/`) and Twilio Media Streams (`/twilio/stream`). Engines are chosen by configuration (`STT_PROVIDER`, `LLM_PROVIDER`, `TTS_PROVIDER`). Built-in mock engines stand in for a provider that is not configured, in development only. The provider adapters have not been load-tested or run in production.

## Pipeline

```
Customer → Twilio Media Streams → PCM16 20ms frames → STT → TurnManager
  → LLM (streaming tokens) → TTS (streaming PCM) → Twilio / WebSocket client
```

Barge-in cancels LLM and TTS immediately. Twilio path adds early energy VAD during `SPEAKING` for sub-150ms interrupt latency.

## Provider configuration

| Layer | Env var | Supported values |
|-------|---------|------------------|
| STT | `STT_PROVIDER` | `deepgram` (more via factory extension) |
| LLM | `LLM_PROVIDER` | `openai`, `anthropic`, `azure_openai`, `groq` |
| TTS | `TTS_PROVIDER` | `elevenlabs`, `openai_audio` |

Factory: `app/voice/factory.py`  
Startup validation: `app/voice/registry.py` (`validate_voice_platform`)

Set `VOICE_REQUIRE_PROVIDERS=true` in production to fail fast on misconfiguration.

## Twilio security

- Inbound webhook: `X-Twilio-Signature` validation (`app/telephony/twilio_validation.py`)
- Media stream: signed `token` + `call_sid` query params with TTL replay protection (`app/telephony/stream_auth.py`)
- Call SID verified on stream `start` event

## Call lifecycle

Extended states: `incoming`, `connecting`, `connected`, `streaming`, `listening`, `processing`, `speaking`, `paused`, `interrupted`, `transferred`, `failed`, `timeout`, `cancelled`, `ended`.

Active calls tracked in `CallSessionRegistry` with heartbeat, concurrency limits, and zombie cleanup.

## Latency measurement

`CallPerformanceMetrics` records:

- First transcript latency
- First token latency
- First audio latency
- End-to-end turn latency

Structured telephony events: `first_user_audio`, `first_token`, `first_audio_sent`, `interruption`, `call_ended`.

## Operations

```bash
STT_PROVIDER=deepgram
LLM_PROVIDER=openai
TTS_PROVIDER=elevenlabs
DEEPGRAM_API_KEY=...
OPENAI_API_KEY=...
ELEVENLABS_API_KEY=...
VOICE_TTS_VOICE_ID=...
VOICE_REQUIRE_PROVIDERS=true
TWILIO_AUTH_TOKEN=...
```

## Load testing

Use `VOICE_MAX_CONCURRENT_CALLS` to cap sessions. Monitor `active_calls` via registry snapshot and telephony logs during soak tests (100/500/1000 concurrent calls).

## Disaster recovery

- LLM failover via `VOICE_LLM_FAILOVER_PROVIDER`
- Pipeline errors trigger fallback TTS and return to `LISTENING`
- Provider outages surface in structured `error` telephony events without crashing the WebSocket
