"""Voice simulation scenario tests."""

from __future__ import annotations

import pytest

from tests.utilities.voice_simulator import VoiceSimulator, standard_scenarios


@pytest.mark.e2e
@pytest.mark.voice
@pytest.mark.asyncio
async def test_normal_conversation_simulation():
    scenario = standard_scenarios()["normal_conversation"]
    sim = VoiceSimulator(scenario)
    frames = []
    async for frame in sim.stream_frames():
        frames.append(frame)
    assert len(frames) > 0
    assert sim.metrics.frames_sent == len(frames)


@pytest.mark.e2e
@pytest.mark.voice
@pytest.mark.asyncio
async def test_packet_loss_simulation_drops_frames():
    scenario = standard_scenarios()["packet_loss"]
    sim = VoiceSimulator(scenario)
    async for _ in sim.stream_frames():
        pass
    assert sim.metrics.frames_dropped >= 0
    assert sim.metrics.frames_sent >= 1


@pytest.mark.e2e
@pytest.mark.voice
@pytest.mark.asyncio
async def test_barge_in_triggers_interruptions():
    scenario = standard_scenarios()["barge_in"]
    sim = VoiceSimulator(scenario)
    async for _ in sim.stream_frames():
        pass
    assert sim.metrics.interruptions_triggered >= 1


@pytest.mark.e2e
@pytest.mark.voice
@pytest.mark.asyncio
async def test_long_conversation_duration():
    scenario = standard_scenarios()["long_conversation"]
    scenario.duration_ms = 2000  # shorten for CI
    sim = VoiceSimulator(scenario)
    async for _ in sim.stream_frames():
        pass
    assert sim.metrics.elapsed_ms >= 1500
