"""PCM16 resampling used for providers with a fixed output rate."""

import math
import struct

from app.voice.audio import Pcm16Resampler, pcm16_duration_seconds


def tone(rate: int, seconds: float, freq: float = 440.0) -> bytes:
    n = int(rate * seconds)
    return struct.pack(f"<{n}h", *(int(8000 * math.sin(2 * math.pi * freq * i / rate)) for i in range(n)))


def test_24k_to_16k_keeps_duration() -> None:
    out = Pcm16Resampler(24000, 16000).process(tone(24000, 1.0))
    assert abs(pcm16_duration_seconds(len(out), 16000) - 1.0) < 0.002


def test_chunked_input_matches_single_call() -> None:
    data = tone(24000, 0.5)
    whole = Pcm16Resampler(24000, 16000).process(data)
    r = Pcm16Resampler(24000, 16000)
    # odd chunk sizes on purpose: samples are split across calls
    pieces = b"".join(r.process(data[i : i + 1001]) for i in range(0, len(data), 1001))
    assert abs(len(pieces) - len(whole)) <= 4
    a = struct.unpack(f"<{len(whole) // 2}h", whole)
    b = struct.unpack(f"<{len(pieces) // 2}h", pieces)
    n = min(len(a), len(b))
    assert max(abs(x - y) for x, y in zip(a[:n], b[:n])) <= 2


def test_same_rate_is_passthrough() -> None:
    data = tone(16000, 0.1)
    assert Pcm16Resampler(16000, 16000).process(data) == data


def test_pitch_is_preserved() -> None:
    """A 440 Hz tone must still be 440 Hz at the new rate (the bug was 24 kHz audio played as 16 kHz)."""
    out = Pcm16Resampler(24000, 16000).process(tone(24000, 1.0, 440.0))
    samples = struct.unpack(f"<{len(out) // 2}h", out)
    crossings = sum(1 for x, y in zip(samples, samples[1:]) if x < 0 <= y)
    assert abs(crossings - 440) <= 3
