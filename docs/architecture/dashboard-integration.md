# Dashboard Backend Integration

Production integration guide for the VOXERA Enterprise Dashboard (`dashboard/`).

## Overview

The dashboard communicates with the backend at `/api/v1` (proxied to `localhost:8000` in development). Authentication uses IAM JWT tokens; tenant-scoped resources use the `tenant_id` from `/iam/auth/me`.

## Authentication Flow

1. **Login** — `POST /iam/auth/login` → stores `access_token` and `refresh_token` in `localStorage`
2. **Bootstrap** — `AuthProvider` calls `GET /iam/auth/me` on load
3. **Refresh** — `apiRequest` retries once on `401` via `POST /iam/auth/refresh`
4. **Logout** — `POST /iam/auth/logout` + clear tokens
5. **Route protection** — `ProtectedRoute` redirects unauthenticated users to `/login`

Permissions are loaded from the IAM profile (`permissions` array on `/iam/auth/me`).

## State Management

| Layer | Technology | Usage |
|-------|------------|-------|
| Server state | TanStack Query | Agents, knowledge, tools, tenants, audit, workflows, dashboard metrics |
| Client session | React Context | Auth, org, IAM profile |
| Real-time ops | Zustand (`liveCallsStore`) | Live calls, WS connection status |
| Query keys | `hooks/queryKeys.ts` | Centralized cache invalidation |

Contexts that wrap Query:
- `AgentsContext` — CRUD via `/tenants/{id}/agents`
- `KnowledgeBaseContext` — upload/list/delete/reprocess via `/tenants/{id}/knowledge`
- `DeveloperContext` — API keys via IAM; webhooks/logs empty (no backend)

## API Mapping

| Dashboard area | Endpoint(s) | Notes |
|----------------|-------------|-------|
| Overview metrics | `/health/deep`, `/tenants/{id}/knowledge/status`, agents, tools, audit | Aggregated in `useDashboardData` |
| Agents | `/tenants/{id}/agents` | Full CRUD |
| Knowledge | `/tenants/{id}/knowledge/*` | Multipart upload, polling while indexing |
| Tools | `/tenants/{id}/tools` | Registry list; execution metrics not yet exposed |
| Workflows | `/tenants/{id}/agents/{aid}/workflow` | Requires agent selection |
| Tenants | `/tenants` | Admin list + create (org onboarding) |
| Audit log | `/tenants/{id}/audit-logs` | Paginated |
| Users | IAM `/iam/organizations/{id}/users` | Invite via IAM |
| API keys | IAM `/iam/organizations/{id}/api-keys` | Create/revoke |
| Billing / Analytics | — | **Not implemented** — empty states |
| Live calls | WebSocket (see below) | Empty until WS connected |

## WebSocket

The dashboard expects an operations WebSocket at:

```
ws(s)://{host}/api/v1/ws/operations?token={jwt}
```

Hook: `hooks/useOperationsWebSocket.ts`  
Store: `stores/liveCallsStore.ts`

**Gap:** The voice pipeline WebSocket exists at `/api/v1/` for call audio, but a dedicated **operations** WebSocket for dashboard live calls is not yet on the backend. Until added, Live Calls shows an empty state with WS status indicator.

When connected, the client handles message types: `call_started`, `call_updated`, `call_ended`, `transcript`, `metrics`.

## Tenant ↔ Organization

- IAM organization records include `tenant_id`
- `OrgContext.tenantId` comes from profile or org record
- `CreateOrganization` creates a backend tenant first (`POST /tenants`), then IAM org

## Error Handling

- Loading: `Skeleton` components on data pages
- Empty: `EmptyState` when lists are empty
- Errors: `ErrorState` with retry (TanStack Query `refetch`)
- Toasts: agent actions, uploads

## Files

```
dashboard/src/
  lib/api/          # REST client, domain APIs
  lib/iam.ts        # IAM auth and org APIs
  lib/mappers.ts    # Backend → UI type mapping
  lib/format.ts     # Duration/relative time helpers
  contexts/         # Auth, Org, Agents, Knowledge, Developer, Billing
  hooks/            # queryKeys, useTenantId, useDashboardData, useOperationsWebSocket
  stores/           # liveCallsStore (Zustand)
```

## Development

```bash
cd dashboard
npm install
npm run dev    # http://localhost:5174
```

Ensure the API server runs on port 8000 (Vite proxy). Set `VITE_API_URL` and `VITE_WS_URL` for non-default deployments.

## Testing

```bash
npm run test
```

Covers format helpers, mappers, and auth token storage. Extend with integration tests against a running API for E2E validation.
