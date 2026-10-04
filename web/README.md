# Voxera Web — Voice Demo

A browser demo for the Voxera voice pipeline. It streams your microphone to the
backend over a WebSocket, shows the transcript and the assistant's reply as they
arrive, and plays the reply audio. You can interrupt the assistant by speaking
(barge-in).

## What it does

- **Microphone streaming.** With the mic on, audio is captured with
  `getUserMedia` (echo cancellation, noise suppression and auto gain on), resampled
  to 16 kHz in an `AudioWorklet`, and sent continuously as binary WebSocket
  messages: PCM16 little-endian, mono, exactly 640 bytes (20 ms) each. The mic is a
  toggle, not push-to-talk; it keeps streaming while the assistant is speaking.
- **Playback.** Binary messages from the server (PCM16 LE mono 16 kHz) are
  scheduled back to back with the Web Audio API, behind an 80 ms jitter buffer.
- **Barge-in.** Speech detection happens on the server. When it sends `tts_clear`,
  the browser stops playback at once and drops everything queued; audio that
  arrives after that is discarded until the next `tts_start`.
- **Provider display and mock notice.** The server names its STT, LLM and TTS
  providers when the session starts. They are shown under *Session status*. If any
  of them is `mock`, a "Mock providers" warning is shown: the mock STT produces
  random words rather than recognising speech, and the mock TTS is a tone.
- **Latency.** *Turn latency* shows the server's latest `turn_metrics`, plus one
  number measured in the browser: from the `final` transcript arriving to the first
  reply audio starting to play. A value that was not measured is shown as `—`.
- **Send test text (development only).** Shown only under `npm run dev`. Sends
  typed text as `dev_test_transcript` or `dev_test_tts`. It does not use the
  microphone or speech recognition.

## Limits

- The microphone needs a secure page: `https://` or `http://localhost`.
- The browser must support `AudioWorklet`.
- Use headphones if the assistant interrupts itself; echo cancellation is the
  browser's and varies by device.
- The capture resampler is linear interpolation behind a simple low-pass filter.
- There is no automatic reconnect. If the connection drops, the mic and playback
  stop and you connect again.

## Stack

- Vite + React + TypeScript
- TailwindCSS (shared preset in `../shared/ui`)
- Native WebSocket
- Web Audio API (`AudioWorklet` capture, `AudioBufferSourceNode` playback)
- Recharts for the metrics chart

## Prerequisites

- Node.js 18+
- The Voxera backend on `http://localhost:8000`

## Quick start

```bash
cd web
npm install
npm run dev
```

Open [http://localhost:5174](http://localhost:5174). Vite moves to the next free
port if 5174 is taken; it prints the address it chose.

## Usage

1. Click **Connect** in the header. In development the WebSocket goes to
   `/api/v1/` on the dev server, which proxies it to `localhost:8000`.
2. Check *Session status* for the providers, and the "Mock providers" warning if
   it appears.
3. Click the microphone button and allow access. Speak; the level bar shows the
   mic is live.
4. Speak while the assistant is talking to interrupt it.
5. Click the microphone button again to stop streaming, or **Disconnect** to end
   the session (this also stops playback and clears the conversation).

## Environment

| Variable      | Description                                         | Default                                          |
|---------------|-----------------------------------------------------|--------------------------------------------------|
| `VITE_WS_URL` | WebSocket URL, e.g. `ws://localhost:8000/api/v1/`   | `/api/v1/` on the page's own host (`ws`/`wss`)   |

```bash
VITE_WS_URL=ws://localhost:8000/api/v1/ npm run dev
```

## Build and preview

```bash
npm run build
npm run preview
```

`npm run build` type-checks (`tsc -b`) and then builds. Preview serves the build
on [http://localhost:4173](http://localhost:4173) by default. Preview has no `/api`
proxy, so set `VITE_WS_URL` at build time to reach the backend from it.

## WebSocket protocol

Audio in both directions: PCM16 little-endian, mono, 16 kHz.

Client → server

- Binary: one 640-byte (20 ms) microphone frame per message.
- `{"type":"dev_test_transcript","text":"…"}`, `{"type":"dev_test_tts","text":"…"}` (development only).

Server → client

- `connection`: conversation id, provider names, audio format.
- `partial`, `final`: transcript of the user's speech.
- `llm_partial`, `llm_final`, `llm_cancelled`: the assistant's reply text.
- `tts_start`, binary audio, `tts_end`: the assistant's reply audio.
- `tts_clear`: stop playback now (barge-in).
- `tts_metrics`, `turn_metrics`: latency figures.
- `error`: shown as an alert.
- `ping`: needs no reply. Unknown message types are ignored.

## Project structure

```
public/
└── pcm-capture-worklet.js   # AudioWorklet: resample to 16 kHz, emit 640-byte PCM16 frames
src/
├── audio/          # MicCapture (mic → frames), PCM16Player (frames → speakers)
├── components/     # Header, Conversation, MicPanel, TurnState, TurnLatency, Metrics, DevControls
├── store/          # VoxeraContext (connection, mic, playback, turns, metrics)
├── types/          # Event types
├── websocket/      # VoxeraWebSocket client
├── App.tsx
├── main.tsx
└── index.css
```

## License

Proprietary — Voxera.
