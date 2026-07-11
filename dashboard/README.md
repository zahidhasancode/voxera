# VOXERA Enterprise Admin Dashboard

Production-grade operating console for enterprise voice AI operations — not a marketing demo.

## Stack

- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** + shared design tokens (`../shared/ui/`)
- **React Router** v6 · **TanStack Query** · **Zustand**
- **Recharts** · **Framer Motion** (subtle) · **React Hook Form** + **Zod**
- **Lucide React** · **Vitest** + Testing Library

## Console Features

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
| **Billing** | Plans, usage, invoices, Stripe portal |

## Run

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:5174](http://localhost:5174). Sign in with your IAM credentials (JWT issued by `/iam/auth/login`).

## Backend integration

The dashboard is wired to the real VOXERA API — no demo auth or mock metrics on connected pages.

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
npm run dev       # Development server
npm run build     # Production build
npm run preview   # Preview production build
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

- Premium, minimal, enterprise-grade (Datadog / Stripe / Cloudflare style)
- Desktop-first, responsive, dark & light themes
- WCAG AA accessibility — keyboard nav, focus states, ARIA
- No glassmorphism or excessive gradients
