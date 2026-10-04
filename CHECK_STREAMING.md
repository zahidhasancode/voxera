# Checking the streaming pipeline

Start the backend (`uvicorn app.main:app --port 8000`), then run the benchmark. It plays recorded
speech into the voice WebSocket at microphone speed and prints what came back and how long it took:

```bash
python scripts/bench_voice_latency.py --url ws://localhost:8000/api/v1/ --turns 5
python scripts/bench_voice_latency.py --barge-in --turns 5
```

Queue health is at `http://localhost:8000/api/v1/metrics`: `voxera_audio_queue_wait_ms` should stay
at a few milliseconds and `voxera_voice_dropped_frames_total` at 0 while a client sends at real-time
cadence. Sending faster than real time fills the 50-frame queue and drops the oldest frames; that
is the intended backpressure behaviour.

Frames are 640 bytes: 20 ms of PCM16 mono at 16 kHz. The protocol is in `docs/voice-protocol.md`.
