# VOXERA Dashboard

The web front end for [VOXERA](https://github.com/zahidhasancode/voxera), a personal real-time voice-agent prototype by MD Zahid Hasan. It contains two things:

- **Project page** (`/`) — a static page describing what the prototype is and what works. This is what the hosted deployment shows.
- **Admin console** (`/login`, `/app/*`) — a UI prototype. It needs the VOXERA backend API running locally. The hosted deployment has no backend, so sign-in does not work there.

This is not a commercial product: there is no company, hosted service, pricing, or support behind it. Plan names and prices in the console's billing screens are placeholder data for the UI prototype.

## Stack

- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** + shared design tokens (`../shared/ui/`)
- **React Router** v6 · **TanStack Query** · **Zustand**
- **Recharts** · **Framer Motion** (subtle) · **React Hook Form** + **Zod**
- **Lucide React** · **Vitest** + Testing Library

## Console screens

| Module | Description |
|--------|-------------|
| **Dashboard** | Today's calls, resolution rate, latency, cost, workflow success, system health |
| **Live call center** | Real-time transcripts, planner/workflow state, supervisor controls |
| **Call details** | Full timeline — planner, verifier, tools, workflow, summary |
| **AI agents** | Card grid with status, language, voice, usage metrics |
| **Knowledge base** | Upload PDF/DOCX/TXT/MD/CSV, indexing, search |
| **Workflow manager** | Visual step viewer, approvals, escalations, rules |
| **Tool registry** | Health, latency, executions, permissions, enable/disable |
| **Tenants** | Companies, plans, usage, storage, API keys |
| **Users** | RBAC roles, invites, sessions |
| **Analytics** | Call volume, resolution, latency, cost trends |
| **Audit logs** | Searchable planner/verifier/workflow/tool events |
| **Billing** | Plans, usage, invoices (placeholder plan data) |

These are screens in a UI prototype. Each one shows data only when the matching backend endpoint is running and returns it; see "Backend integration" below for what is connected.

## Run

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) (the port set in `vite.config.ts`; Vite picks the next free port if 5173 is taken). The dev server proxies `/api` to the backend at `http://localhost:8000`, so start the backend first — see the [repository README](../README.md).

Sign in to the console with credentials from your local backend (JWT issued by `/iam/auth/login`). If the backend is not running, the login page shows an error.

## Backend integration

Connected pages call the VOXERA API directly; they do not fall back to mock data.

| Connected | Pending backend |
|-----------|-----------------|
| IAM login, refresh, logout | Billing usage history |
| Agents, knowledge, tools | Analytics time-series |
| Tenants, audit logs, workflows | Operations WebSocket (live calls) |
| Org users, API keys | Webhooks, notifications |

See [docs/architecture/dashboard-integration.md](../docs/architecture/dashboard-integration.md) for API mapping, auth flow, and WebSocket notes.

## Environment

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API base (default: `/api/v1` via Vite proxy) |
| `VITE_WS_URL` | Operations WebSocket for live calls |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key (optional) |

## Scripts

```bash
npm run dev       # Development server (port 5173)
npm run build     # Type-check and build the static bundle into dist/
npm run preview   # Serve the built bundle locally
npm run test      # Vitest unit tests
```

## Architecture

See [docs/architecture/enterprise-admin-dashboard.md](../docs/architecture/enterprise-admin-dashboard.md) for:

- Layout and navigation structure
- Real-time WebSocket architecture
- State management guide (Zustand + TanStack Query)
- Component library reference
- Folder structure

## Design System

Reusable components in `src/components/ui/`:

Button, Card, Badge, Table, Tabs, Dialog, Drawer, StatCard, MetricCard, Timeline, LogViewer, CodeBlock, SearchInput, Progress, Tooltip, Toast, Skeleton, EmptyState, ErrorState

Shared tokens: `shared/ui/tokens.css`, `shared/ui/tailwind.preset.js`

## Real-Time

Live call center uses `useOperationsWebSocket` → `liveCallsStore` (Zustand). When the operations WebSocket is unavailable, the UI shows an empty live-calls state (no simulated mock data).

## Design Principles

- Minimal, dense operations-console style
- Desktop-first, responsive, dark & light themes
- Keyboard navigation, focus states, and ARIA labels on shared components (not audited)
- No glassmorphism or excessive gradients
