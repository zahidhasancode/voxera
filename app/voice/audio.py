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
