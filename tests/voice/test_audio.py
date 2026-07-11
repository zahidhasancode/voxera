"""Voice audio utility tests."""

from app.voice.audio import chunk_pcm_bytes, normalize_pcm16, pcm_frame_energy


def test_chunk_pcm_bytes_returns_remainder() -> None:
    data = b"\x01" * 1000
    frames, remainder = chunk_pcm_bytes(data, 640)
    assert len(frames) == 1
    assert len(frames[0]) == 640
    assert len(remainder) == 360


def test_pcm_frame_energy_nonzero() -> None:
    frame = (b"\xff\x7f" * 100)
    assert pcm_frame_energy(frame) > 0


def test_normalize_pcm16_preserves_frame_length() -> None:
    frame = b"\x00\x10" * 160
    normalized = normalize_pcm16(frame)
    assert len(normalized) == len(frame)
