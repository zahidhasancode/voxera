# Voxera Web — Real-Time Voice AI Dashboard

Production-grade demo dashboard for the Voxera real-time voice AI platform. Built for investor demos, startup showcases, and senior engineering interviews.

## Stack

- **Vite** + **React** + **TypeScript**
- **TailwindCSS** for styling
- **Native WebSocket** (no socket.io)
- **Web Audio API** for PCM16 playback
- **Recharts** for metrics

## Prerequisites

- **Node.js** 18+
- **Voxera backend** running on `http://localhost:8000`

## Quick start

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Usage

1. **Connect** — Click **Connect** in the header to open the WebSocket to `ws://localhost:8000/api/v1/`.
2. **Dev transcript** — In **Developer Controls**, enter text and click **Send** to send `{"type":"dev_test_transcript","text":"..."}`.
3. **Dev TTS** — Enter text and click **TTS** to send `{"type":"dev_test_tts","text":"..."}` (TTS-only).
4. **Clear** — Click **Clear conversation** to reset the conversation panel.

## Environment

| Variable      | Description                                      | Default                         |
|---------------|--------------------------------------------------|---------------------------------|
| `VITE_WS_URL` | WebSocket URL (e.g. `ws://localhost:8000/api/v1/`) | `ws://${window.location.host}/api/v1/` |

Example:

```bash
VITE_WS_URL=ws://localhost:8000/api/v1/ npm run dev
```

## Build & preview

```bash
npm run build
npm run preview
```

Preview serves the production build (default: [http://localhost:4173](http://localhost:4173)).

## Backend contract

- **WebSocket:** `ws://localhost:8000/api/v1/`
- **JSON events:** `connection`, `ping`, `llm_partial`, `llm_final`, `llm_cancelled`, `tts_metrics`, transcript `partial`/`final`
- **Binary:** Raw PCM16 mono, 16 kHz, 20 ms frames (640 bytes)

## Project structure

```
src/
├── audio/          # PCM16 → Web Audio API playback
├── components/     # Header, Conversation, Audio, TurnState, Metrics, DevControls
├── store/          # VoxeraContext (connection, turns, metrics)
├── types/          # Event types
├── websocket/      # VoxeraWebSocket client
├── App.tsx
├── main.tsx
└── index.css
```

## License

Proprietary — Voxera.
