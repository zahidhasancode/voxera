"""Unit tests for Twilio μ-law → PCM16 16 kHz conversion."""

import pytest

from app.telephony.audio_convert import (
    PCM16_WIDTH,
    TARGET_PCM_RATE,
    TWILIO_MULAW_RATE,
    convert_twilio_audio,
)


class TestConvertTwilioAudio:
    """Tests for convert_twilio_audio(payload: bytes) -> bytes."""

    def test_empty_returns_empty(self) -> None:
        assert convert_twilio_audio(b"") == b""

    def test_output_length_is_four_times_input(self) -> None:
        # 1 μ-law byte → 2 bytes PCM16 → 4 bytes after 2× resample
        payload = b"\xff" * 10
        out = convert_twilio_audio(payload)
        assert len(out) == len(payload) * 4

    def test_output_is_pcm16_little_endian(self) -> None:
        # μ-law 0xFF decodes to silence (0) in G.711; 0x7F similar
        payload = b"\xff\xff"
        out = convert_twilio_audio(payload)
        assert len(out) == 8
        # All samples should be 0 (silence) for 0xFF input
        for i in range(0, len(out), 2):
            sample = int.from_bytes(out[i : i + 2], "little", signed=True)
            assert sample == 0

    def test_chunk_roundtrip_length(self) -> None:
        # Typical Twilio chunk: 20 ms at 8 kHz = 160 μ-law bytes
        # → 320 bytes PCM16 8k → 640 bytes PCM16 16k
        payload = bytes(160)
        out = convert_twilio_audio(payload)
        assert len(out) == 160 * 4  # 640

    def test_large_payload(self) -> None:
        payload = bytes(8000)  # 1 second of μ-law
        out = convert_twilio_audio(payload)
        assert len(out) == 8000 * 4
        assert len(out) % (PCM16_WIDTH * 2) == 0
