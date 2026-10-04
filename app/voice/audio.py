"""PCM audio utilities for voice streaming."""

from __future__ import annotations

import struct


def pcm_frame_energy(frame: bytes) -> float:
    """Mean absolute PCM16 sample value (0–32767)."""
    if len(frame) < 2:
        return 0.0
    n = len(frame) // 2
    total = 0
    for i in range(n):
        total += abs(struct.unpack_from("<h", frame, i * 2)[0])
    return total / n if n else 0.0


def _pcm_rms(frame: bytes) -> float:
    if len(frame) < 2:
        return 0.0
    n = len(frame) // 2
    total = 0.0
    for i in range(n):
        sample = struct.unpack_from("<h", frame, i * 2)[0]
        total += float(sample * sample)
    return (total / n) ** 0.5 if n else 0.0


def normalize_pcm16(frame: bytes, target_rms: float = 3000.0) -> bytes:
    """Light normalization to improve STT consistency without clipping."""
    if len(frame) < 2:
        return frame
    rms = _pcm_rms(frame)
    if rms <= 0:
        return frame
    factor = min(4.0, target_rms / rms)
    if 0.85 <= factor <= 1.15:
        return frame
    samples = struct.unpack(f"<{len(frame) // 2}h", frame)
    normalized = [max(-32768, min(32767, int(sample * factor))) for sample in samples]
    return struct.pack(f"<{len(normalized)}h", *normalized)


def chunk_pcm_bytes(data: bytes, frame_bytes: int) -> tuple[list[bytes], bytes]:
    """Split PCM into fixed-size frames; return frames and trailing remainder."""
    if frame_bytes <= 0:
        return ([data] if data else []), b""
    frames: list[bytes] = []
    idx = 0
    while idx + frame_bytes <= len(data):
        frames.append(data[idx : idx + frame_bytes])
        idx += frame_bytes
    return frames, data[idx:]


class Pcm16Resampler:
    """Streaming PCM16 mono resampler (linear interpolation).

    Keeps state between calls so audio that arrives in arbitrary chunks is
    resampled without clicks at the chunk boundaries. Used for providers that
    return a fixed rate (OpenAI speech returns 24 kHz) when the pipeline runs
    at another rate (16 kHz).
    """

    def __init__(self, src_rate: int, dst_rate: int) -> None:
        if src_rate <= 0 or dst_rate <= 0:
            raise ValueError("sample rates must be positive")
        self._step = src_rate / dst_rate
        self._same = src_rate == dst_rate
        self._pos = 0.0  # position of the next output sample, in source samples
        self._last: int | None = None  # last source sample of the previous chunk
        self._odd = b""  # a single byte left over from an odd-length chunk

    def process(self, chunk: bytes) -> bytes:
        """Resample one chunk; returns PCM16 at the destination rate."""
        if not chunk:
            return b""
        data = self._odd + chunk
        if len(data) % 2:
            data, self._odd = data[:-1], data[-1:]
        else:
            self._odd = b""
        if self._same or not data:
            return data
        samples = list(struct.unpack(f"<{len(data) // 2}h", data))
        if self._last is not None:
            samples.insert(0, self._last)
        out: list[int] = []
        pos = self._pos
        last_index = len(samples) - 1
        while pos < last_index:
            i = int(pos)
            frac = pos - i
            out.append(int(samples[i] + (samples[i + 1] - samples[i]) * frac))
            pos += self._step
        self._pos = pos - last_index
        self._last = samples[-1]
        return struct.pack(f"<{len(out)}h", *out)


def pcm16_duration_seconds(num_bytes: int, sample_rate: int) -> float:
    """Playback time of PCM16 mono audio of the given size."""
    if sample_rate <= 0:
        return 0.0
    return (num_bytes // 2) / float(sample_rate)
