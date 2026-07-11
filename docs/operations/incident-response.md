# Incident Response Guide

## Severity Levels

| SEV | Definition | Response |
|-----|------------|----------|
| SEV1 | Complete outage, no calls | Immediate, all hands |
| SEV2 | Degraded voice/API, partial outage | < 15 min acknowledge |
| SEV3 | Non-critical feature degraded | Next business day |
| SEV4 | Cosmetic / monitoring noise | Backlog |

## First 5 Minutes

1. Confirm impact: `curl /api/v1/health/deep`
2. Check recent deploys (Helm history / compose logs)
3. Check Prometheus alerts
4. Page voice provider status pages (OpenAI, Deepgram, ElevenLabs, Twilio)

## Common Incidents

### API 503 on /ready

**Cause:** Database unreachable, knowledge storage not writable, provider validation failed.

**Actions:**
```bash
kubectl logs -l app.kubernetes.io/component=api --tail=200
# Verify DATABASE_URL, postgres health
# Check KNOWLEDGE_STORAGE_PATH mount
```

### High voice latency

**Cause:** Provider degradation, queue backlog, insufficient API replicas.

**Actions:**
- Scale API: `kubectl scale deployment voxera-api --replicas=N`
- Check `voxera_voice_queue_depth` metric
- Failover provider if configured (`VOICE_LLM_FAILOVER_PROVIDER`)

### Failed deployment

**Actions:**
```bash
helm rollback voxera --namespace voxera-prod
kubectl rollout undo deployment/voxera-api
```

### Database failure

See [Backup & Restore](./backup-restore.md). Fail over to replica or restore from latest backup.

## Communication Template

```
[SEV-X] VOXERA — <brief title>
Impact: <who/what>
Start: <UTC time>
Status: Investigating | Mitigating | Resolved
Next update: <time>
```

## Post-Incident

1. Timeline document within 48h
2. Root cause + corrective actions
3. Update runbooks if gap found
