# VOXERA Admin Dashboard

Production-ready SaaS admin dashboard for VOXERA — real-time Voice AI for enterprise customer support.

## Stack

- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** (dark-first theme)
- **React Router** v6
- **Stripe** (billing — add `VITE_STRIPE_PUBLISHABLE_KEY` for live billing)
- **Recharts** (analytics)
- **Lucide React** (icons)

## Features

- **Multi-tenant:** Organization switcher; per-org context
- **RBAC:** Admin, member, viewer (enforced in UI; wire to API as needed)
- **Billing:** Plan display and Stripe Customer Portal placeholder
- **Usage:** Voice minutes, conversations, API calls
- **Agents:** List and manage voice AI agents
- **Knowledge base:** Articles and sources
- **API keys:** List, create, revoke
- **Analytics:** Conversation and voice usage charts
- **Organization & Settings:** Profile, members, account settings

## Run

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:5174](http://localhost:5174). Sign in with any email/password (demo auth).

## Env

| Variable | Description |
|----------|-------------|
| `VITE_STRIPE_PUBLISHABLE_KEY` | Stripe publishable key for billing (optional) |
| `VITE_API_URL` | Backend API base URL (optional) |

## Build

```bash
npm run build
npm run preview
```

## Design

- Dark-first, calm enterprise UI (Stripe / Vercel / Linear style)
- Strong typography (Inter), clear spacing, subtle transitions
- No flashy animations; investor-demo quality
