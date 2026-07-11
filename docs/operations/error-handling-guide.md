# Error Handling Guide

All VOXERA API errors use a single envelope format. Clients should parse `error.code` for programmatic handling and display `error.message` to users.

## Response shape

```json
{
  "success": false,
  "error": {
    "code": "not_found",
    "message": "Resource not found",
    "details": null,
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-07-11T00:00:00+00:00",
    "documentation_url": "https://docs.voxera.ai/errors/not_found"
  }
}
```

## Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `validation_error` | 400/422 | Invalid input |
| `not_found` | 404 | Resource missing |
| `conflict` | 409 | Duplicate or constraint violation |
| `authentication_error` | 401 | Missing or invalid credentials |
| `authorization_error` | 403 | Insufficient permissions |
| `rate_limit_exceeded` | 429 | Too many requests |
| `request_timeout` | 504 | Request exceeded deadline |
| `database_error` | 503 | Database failure |
| `service_unavailable` | 503 | Dependency unavailable / shutdown |
| `tool_error` | 4xx/5xx | Tool framework errors |
| `workflow_error` | 4xx/5xx | Workflow engine errors |
| `planner_error` | 4xx/5xx | Planner errors |
| `verifier_error` | 4xx/5xx | Verifier errors |
| `memory_error` | 403/404 | Memory access errors |
| `retrieval_error` | 422 | RAG validation errors |
| `internal_error` | 500 | Unexpected server error |

## Client retry guidance

| Code | Retry? |
|------|--------|
| `rate_limit_exceeded` | Yes — respect `Retry-After` header |
| `request_timeout` | Yes — with backoff |
| `service_unavailable` | Yes — with backoff |
| `database_error` | Yes — limited retries |
| `authentication_error` | No — refresh token or re-authenticate |
| `authorization_error` | No |
| `validation_error` | No — fix request |
| `internal_error` | No — contact support with `request_id` |

## Correlating with logs

Include `request_id` from the error response when contacting support. Server logs index on `request_id` and `correlation_id`.

## Route-level vs global handling

Domain routes may still use `map_domain_errors()` in try/except blocks. All exceptions ultimately pass through global handlers if unhandled, producing the same envelope.
