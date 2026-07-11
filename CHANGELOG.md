# Changelog

All notable changes to VOXERA are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
