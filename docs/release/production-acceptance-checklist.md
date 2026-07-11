# Production Acceptance Checklist

Customer / design partner sign-off criteria for RC1 deployment.

## Functional

- [ ] User can log in via dashboard
- [ ] Organization and tenant accessible
- [ ] Agent can be created and configured
- [ ] Knowledge document can be uploaded and processed
- [ ] Voice WebSocket session establishes and streams audio
- [ ] Integration can be connected (OAuth or API key provider)
- [ ] Audit log shows administrative actions

## Non-functional

- [ ] API P95 latency <800ms (health/knowledge endpoints)
- [ ] Voice first-audio latency <1500ms (configured providers)
- [ ] Zero critical security findings in pre-deploy scan
- [ ] Backups configured and restore tested
- [ ] Monitoring dashboards accessible to operations team

## Documentation delivered

- [ ] Deployment guide
- [ ] Environment variables reference
- [ ] Incident response contacts
- [ ] Known issues document acknowledged

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Customer technical lead | | | |
| VOXERA release manager | | | |
| VOXERA SRE | | | |
