# Voice WebSocket protocol

Endpoint: `ws://<host>/api/v1/` (add `?token=<JWT>` outside development).

Audio in both directions is raw PCM16 little-endian, mono, 16 kHz, in 20 ms frames (640 bytes).
The server states this in its first message; a client should read it rather than assume it.

## Client → server

| Message | Meaning |
|---|---|
| binary, 640 bytes | One 20 ms audio frame. Send continuously while the microphone is on, at real-time cadence. |
| `{"type":"ping"}` | Answered with `{"type":"pong"}`. |
| `{"type":"dev_test_transcript","text":"…"}` | Development only: behave as if the user had said the text. |
| `{"type":"dev_test_tts","text":"…"}` | Development only: speak the text without calling the LLM. |

The two `dev_test_*` messages are refused with `error` / `dev_message_disabled` unless
`ENVIRONMENT=development`, because they make the server call paid providers with arbitrary text.

## Server → client

| Message | Meaning |
|---|---|
| `{"type":"connection","status":"connected","conversation_id","providers":{"stt","llm","tts"},"audio":{"sample_rate","frame_ms","encoding"}}` | First message. A provider named `mock` is the built-in development engine. |
| `{"type":"partial"\|"final","utterance_id","transcript","confidence","timestamp"}` | Speech recognition. `final` ends the user's turn. |
| `{"type":"llm_partial","utterance_id","token","token_index","accumulated"}` | One LLM token. |
| `{"type":"llm_final","utterance_id","text","metrics"}` | The complete answer text. Speech has usually started before this. |
| `{"type":"llm_cancelled","utterance_id","partial_text","metrics"}` | Generation was stopped (barge-in or disconnect). |
| `{"type":"tts_start","utterance_id"}` | Reply audio follows as binary frames. |
| binary | Reply audio, PCM16 16 kHz. Sent at most `VOICE_TTS_MAX_LEAD_MS` ahead of playback. |
| `{"type":"tts_end","utterance_id"}` | The reply has been sent and has had time to play. |
| `{"type":"tts_clear","utterance_id","reason"}` | **Stop playback now and discard queued audio.** `reason` is `barge_in`, `superseded` or `closed`. Ignore binary frames until the next `tts_start`. |
| `{"type":"barge_in","server_stop_ms"}` | The user interrupted; how long the server took to stop. |
| `{"type":"tts_metrics","utterance_id","metrics":{"time_to_first_audio_ms","frame_count","segments","audio_ms","interrupted"}}` | Summary of one reply's speech. |
| `{"type":"turn_metrics","utterance_id","transcript_final_to_llm_first_token_ms","transcript_final_to_first_segment_ms","transcript_final_to_first_audio_ms","llm_first_token_to_first_audio_ms","interrupted"}` | Timing of one turn; a value is `null` if that stage was not reached. |
| `{"type":"error","code","message"}` | `voice_providers_unavailable`, `llm_failed`, `tts_failed`, `dev_message_disabled`. |
| `{"type":"ping"}` | Keep-alive; no reply needed. |

Unknown message types should be ignored.

## Order of events in a normal turn

```
partial … partial  final
                   llm_partial …            (tokens)
                   tts_start  <audio…>      (first sentence is spoken while tokens still arrive)
                   llm_final
                   <audio…>  tts_end  tts_metrics  turn_metrics
```

## Barge-in

While a reply is being generated or played, any `partial` from the user stops it:

```
<audio…>  partial   llm_cancelled?  tts_clear  barge_in  tts_metrics  turn_metrics(interrupted=true)
```
