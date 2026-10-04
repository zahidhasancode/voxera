# Changelog

All notable changes to VOXERA are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Barge-in now stops a reply while it is playing, not only while it is being generated. The system
  turn used to end as soon as the LLM finished.
- The inbound audio dispatcher no longer runs on a fixed 20 ms timer. It could never catch up, so
  the queue filled within a minute, added about one second to every turn and dropped frames.
- OpenAI speech (24 kHz) is resampled to the pipeline rate instead of being played as 16 kHz.
- Deepgram: only `speech_final` (or `UtteranceEnd`) ends the user's turn; a finished segment no
  longer does.
- A final transcript with no partial before it is answered instead of being dropped.
- Phone calls return to listening after a reply and answer the second turn.
- Voice connections are closed on shutdown; a provider error at connect time no longer leaks the connection.
- `jsonschema` added to the requirements; `.gitignore` no longer hides `dashboard/src/lib` and `deploy/env`.

### Added
- Sentence-by-sentence speech: TTS starts on the first finished sentence of the LLM stream.
- Conversation history in the voice path.
- Real-time pacing of reply audio, and a `tts_clear` event for clients.
- Per-turn latency (`turn_metrics`), rolling percentiles at `/api/v1/metrics`, and
  `scripts/bench_voice_latency.py`.
- Live microphone capture and playback in the browser demo.
- Mock engines as an explicit development fallback, named in the connection message.

### Changed
- `dev_test_*` WebSocket messages are accepted in development only.
- `voxera_voice_latency_ms` (which was queue wait) is now `voxera_audio_queue_wait_ms`.
- CI runs only jobs that pass locally: ruff, unit tests, and the two frontend builds.

### Removed
- The unmounted `/ws/audio` pipeline (`app/services`, `app/models`) and its tests, the unused
  `twilio_stt_bridge.py`, and the deploy workflows that only printed text.

## [1.0.0-RC1] - 2026-07-11

### Release Candidate — Enterprise Platform

First release candidate certifying VOXERA for design partner onboarding and controlled production pilots.

#### Platform

- Multi-tenant enterprise REST API under `/api/v1/tenants/{tenant_id}/`
- Enterprise IAM (JWT, API keys, RBAC, organizations, MFA hooks)
- Enterprise Dashboard (React) with live operations, agents, knowledge, workflows, tools, integrations
- Enterprise Integration Platform (49 providers, OAuth, webhooks, sync engine)

#### Cognitive Stack

- Planner Agent (intent classification, reasoning loop, policy engine)
- Verifier Agent (hallucination detection, compliance, risk engine)
- Workflow Engine (rules, approvals, escalation, routing)
- Tool Registry and execution framework
- Enterprise Knowledge Platform (ingestion pipeline, vector stores, embeddings)
- Enterprise Memory System (working memory, summarization, compression)

#### Voice & Telephony

- Production voice infrastructure (STT/LLM/TTS streaming, barge-in)
- Twilio telephony integration (WebSocket media streams)
- WebSocket voice pipeline with bounded queues and metrics

#### Operations

- Docker multi-stage production images (non-root)
- Docker Compose (dev, prod, monitoring stacks)
- Kubernetes Helm chart with HPA, PDB, NetworkPolicy, ServiceMonitor
- GitHub Actions CI/CD (lint, test, security scan, image build, SBOM)
- Prometheus metrics, Grafana/Jaeger scaffolding
- Alembic migrations 001–010

#### Testing

- 261+ automated Python tests (unit, integration, e2e, security, chaos)
- Golden dataset evaluation (7 domains)
- Voice simulation framework
- k6 load test scripts
- Dashboard Vitest suite

#### RC1 Hardening

- Fixed missing exception imports in authentication middleware
- Fixed post-auth rate limiter state persistence (module-level limiters)
- Removed duplicate dependency import

### Known Limitations (RC1)

- Coverage gate at 65% (target 90% for GA)
- Per-route RBAC not yet enforced on all tenant REST endpoints
- OpenTelemetry application instrumentation not wired
- Twilio STT bridge uses mock engine when real provider not configured
- Redis-backed rate limits and distributed tracing planned post-RC1

[1.0.0-RC1]: https://github.com/voxera/voxera/releases/tag/v1.0.0-RC1
