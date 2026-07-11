# Voice Simulation Guide

## Overview

`tests/utilities/voice_simulator.py` provides deterministic PCM frame generation with configurable network and conversational conditions.

## Built-in scenarios

| Scenario | Conditions simulated |
|----------|---------------------|
| `normal_conversation` | Standard speech rate, clean line |
| `fast_speech` | Elevated speech rate |
| `slow_speech` | Reduced speech rate |
| `noisy_line` | Background noise mix |
| `packet_loss` | Dropped frames + network delay |
| `barge_in` | Customer interruption events |
| `long_conversation` | Extended duration, multi-speaker |
| `language_switch` | Primary + secondary language tags |

## Usage

```python
from tests.utilities.voice_simulator import VoiceSimulator, standard_scenarios

scenario = standard_scenarios()["barge_in"]
sim = VoiceSimulator(scenario)

async for frame in sim.stream_frames():
    await send_to_asr(frame)

print(sim.metrics.frames_sent, sim.metrics.interruptions_triggered)
```

## Custom scenarios

```python
from tests.utilities.voice_simulator import VoiceScenario, SpeechRate, VoiceSimulator

scenario = VoiceScenario(
    name="custom",
    speech_rate=SpeechRate.FAST,
    packet_loss_rate=0.05,
    network_delay_ms=80,
    barge_in_enabled=True,
    interruption_at_ms=[500, 1500],
    duration_ms=5000,
)
```

## Metrics collected

- `frames_sent` / `frames_dropped`
- `interruptions_triggered`
- `elapsed_ms` / `total_latency_ms`

## CI tests

`tests/e2e/voice/test_voice_simulation.py` validates scenario execution without requiring live Twilio/STT providers.

## Extending to live voice

Wire `VoiceSimulator.run_with_handler()` to existing WebSocket ASR tests in `tests/test_e2e_asr.py` when `VOICE_REQUIRE_PROVIDERS=true` in staging.
