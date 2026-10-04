# Testing

## Automated tests

```bash
pip install -r requirements-dev.txt
python -m pytest -m "not integration and not slow"
ruff check app/ tests/ scripts/
```

No network and no database are needed. Tests that need PostgreSQL are marked `integration` and are
skipped by the command above; run them with `DATABASE_URL` set and `alembic upgrade head` applied:

```bash
python -m pytest -m integration
```

## What the voice tests cover

`tests/voice/` and `tests/telephony_voice/` use deterministic fake engines (`tests/voice/fakes.py`):

| File | Covers |
|---|---|
| `test_voice_session.py` | speech starts before the LLM finishes; the system turn lasts until playback ends; barge-in during generation and during playback; history; turn metrics; LLM failure |
| `test_tts_consumer.py` | sentence queue, real-time pacing, stop and `tts_clear` |
| `test_sentence_chunker.py` | sentence boundaries, decimals, abbreviations, long clauses |
| `test_deepgram_parse.py` | segment results versus end of speech |
| `test_resampler.py` | 24 kHz to 16 kHz, chunk boundaries, pitch |
| `test_websocket_voice.py` | the mounted endpoint end to end with the mock engines |
| `telephony_voice/test_call_session_turns.py` | phone session: streamed reply, second turn, Twilio `clear` on barge-in |

## Manual checks

- Latency and barge-in against a running server: see [CHECK_STREAMING.md](CHECK_STREAMING.md).
- Browser demo: `cd web && npm run dev`, open http://localhost:5174, connect, turn the microphone on.
  With mock providers the transcript is random words and the reply is a tone; the page says so.

## Not covered

- The provider adapters against the live services (Deepgram, OpenAI, Anthropic, Groq, ElevenLabs).
- Twilio Media Streams against Twilio.
- The browser microphone path (no automated browser audio test).
