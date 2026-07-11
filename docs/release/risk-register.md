# RC1 Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| R-01 | Unauthorized tenant API access (missing per-route RBAC) | Medium | Critical | Network isolation; service account scoping; GA RBAC rollout | Security |
| R-02 | Mock STT on Twilio production calls | High | High | Require STT provider config; pre-flight voice checklist | Voice |
| R-03 | Rate limit bypass under multi-pod | Medium | Medium | Start with 1–2 API replicas; Redis in GA | SRE |
| R-04 | Credential exposure via misconfigured env | Low | Critical | `validate_security_settings()` blocks prod defaults | Platform |
| R-05 | Integration webhook replay without signature | Low | High | Signature validation + idempotency ledger | Integrations |
| R-06 | Database migration failure on deploy | Low | High | Staging migration test; backup before upgrade | SRE |
| R-07 | Coverage gaps hide regressions | Medium | Medium | Mandatory QA suite on PR; ratchet to 80% | QA |
| R-08 | Public metrics endpoint scraped externally | Medium | Low | NetworkPolicy; internal-only ingress | SRE |
| R-09 | In-process job loss on crash | Low | Medium | DB-persisted job tables; retry logic | Platform |
| R-10 | Dependency CVE in aging stack | Medium | Medium | Manual audit; pip-audit review each release | Security |

## Risk appetite (RC1)

Accept **Medium/Low** risks with documented mitigations. **Critical** risks R-01 and R-04 require compensating controls before design partner data access.
