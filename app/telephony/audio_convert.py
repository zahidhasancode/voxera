"""Twilio μ-law (8 kHz) to PCM16 (16 kHz) conversion.

Uses Python stdlib (audioop when available); pure-Python fallback for
environments where audioop is removed (e.g. Python 3.13+). Low-latency,
chunk-friendly, and unit-testable.
"""

import struct

# Sample rates (Hz)
TWILIO_MULAW_RATE = 8000
TARGET_PCM_RATE = 16000

# PCM16 sample width in bytes
PCM16_WIDTH = 2

try:
    import audioop
except ImportError:
    audioop = None  # type: ignore


def _ulaw_to_pcm16_audioop(payload: bytes) -> bytes:
    """μ-law to PCM16 using audioop (stdlib)."""
    return audioop.ulaw2lin(payload, PCM16_WIDTH)


def _ulaw_to_pcm16_pure(payload: bytes) -> bytes:
    """μ-law to PCM16 using G.711 decode (pure Python, no deps)."""
    # G.711 μ-law expansion: 8-bit → 16-bit linear (little-endian).
    out = bytearray(len(payload) * PCM16_WIDTH)
    for i, u in enumerate(payload):
        u = u ^ 0xFF
        sign = u & 0x80
        exponent = (u >> 4) & 0x07
        mantissa = u & 0x0F
        sample = ((mantissa << 3) + 0x84) << exponent
        sample -= 0x84
        if sign:
            sample = -sample
        # Scale 14-bit range to 16-bit (×4, clamp)
        sample = max(-32768, min(32767, sample * 4))
        struct.pack_into("<h", out, i * PCM16_WIDTH, sample)
    return bytes(out)


def _resample_8k_to_16k_audioop(pcm16_8k: bytes) -> bytes:
    """Resample PCM16 8 kHz → 16 kHz using audioop.ratecv."""
    out, _ = audioop.ratecv(
        pcm16_8k,
        PCM16_WIDTH,
        1,
        TWILIO_MULAW_RATE,
        TARGET_PCM_RATE,
        None,  # state (one-shot)
    )
    return out


def _resample_8k_to_16k_pure(pcm16_8k: bytes) -> bytes:
    """Resample PCM16 8 kHz → 16 kHz by 2× upsample (duplicate each sample). Low latency."""
    n = len(pcm16_8k) // PCM16_WIDTH
    out = bytearray(n * 2 * PCM16_WIDTH)
    for i in range(n):
        offset_in = i * PCM16_WIDTH
        offset_out = i * 2 * PCM16_WIDTH
        sample = pcm16_8k[offset_in : offset_in + PCM16_WIDTH]
        out[offset_out : offset_out + PCM16_WIDTH] = sample
        out[offset_out + PCM16_WIDTH : offset_out + 2 * PCM16_WIDTH] = sample
    return bytes(out)


def _ulaw_to_pcm16(payload: bytes) -> bytes:
    """Dispatch μ-law → PCM16; use audioop if available else pure Python."""
    if audioop is not None:
        return _ulaw_to_pcm16_audioop(payload)
    return _ulaw_to_pcm16_pure(payload)


def _resample_8k_to_16k(pcm16_8k: bytes) -> bytes:
    """Resample 8 kHz → 16 kHz by 2× duplicate. Deterministic length, low latency."""
    # Always use pure 2× duplicate so output length is exactly 2× input (no audioop.ratecv state quirks).
    return _resample_8k_to_16k_pure(pcm16_8k)


def convert_twilio_audio(payload: bytes) -> bytes:
    """Convert Twilio μ-law 8 kHz mono to PCM16 16 kHz mono.

    Input: raw μ-law bytes (e.g. from Twilio Media Stream media.payload after base64 decode).
    Output: PCM16 little-endian, 16 kHz, mono; ready for STT or other processing.

    Low latency: processes in one pass; no heavy deps. Empty input returns empty bytes.
    """
    if not payload:
        return b""
    pcm16_8k = _ulaw_to_pcm16(payload)
    return _resample_8k_to_16k(pcm16_8k)


# --- Outbound: PCM16 16 kHz → μ-law 8 kHz (for Twilio media send) ---


def _pcm16_to_ulaw_audioop(pcm16: bytes) -> bytes:
    """PCM16 to μ-law using audioop (stdlib)."""
    return audioop.lin2ulaw(pcm16, PCM16_WIDTH)


def _pcm16_to_ulaw_pure(pcm16: bytes) -> bytes:
    """PCM16 to μ-law using G.711 encode (pure Python). Input little-endian 16-bit samples."""
    out = bytearray(len(pcm16) // PCM16_WIDTH)
    for i in range(0, len(pcm16), PCM16_WIDTH):
        sample = struct.unpack_from("<h", pcm16, i)[0]
        sign = 0x80 if sample < 0 else 0
        if sample < 0:
            sample = -sample
        # 16-bit → 14-bit range (G.711), then add BIAS for segment search
        sample = min(sample >> 2, 0x1FFF) + 0x84
        exponent = 0
        for e, end in enumerate(_SEG_ULAW_END):
            if sample <= end:
                exponent = e
                break
        else:
            exponent = 7
        mantissa = (sample >> (exponent + 3)) & 0x0F
        u = (~(sign | (exponent << 4) | mantissa)) & 0xFF
        out[i // PCM16_WIDTH] = u
    return bytes(out)


# Segment upper bounds for μ-law encoding (14-bit + 0x84): 0xFC<<e for e=0..7
_SEG_ULAW_END = (0xFC, 0x1F8, 0x3F0, 0x7E0, 0xFC0, 0x1F80, 0x3F00, 0x7E00)


def _pcm16_to_ulaw(pcm16: bytes) -> bytes:
    """Dispatch PCM16 → μ-law; use audioop if available else pure Python."""
    if audioop is not None:
        return _pcm16_to_ulaw_audioop(pcm16)
    return _pcm16_to_ulaw_pure(pcm16)


def _resample_16k_to_8k_pure(pcm16_16k: bytes) -> bytes:
    """Downsample PCM16 16 kHz → 8 kHz by taking every other sample. Low latency."""
    # 320 samples @ 16k → 160 samples @ 8k
    n_out = len(pcm16_16k) // (PCM16_WIDTH * 2)
    out = bytearray(n_out * PCM16_WIDTH)
    for i in range(n_out):
        src_off = i * 2 * PCM16_WIDTH
        out[i * PCM16_WIDTH : (i + 1) * PCM16_WIDTH] = pcm16_16k[src_off : src_off + PCM16_WIDTH]
    return bytes(out)


def pcm16_16k_to_twilio_audio(pcm16_16k: bytes) -> bytes:
    """Convert PCM16 16 kHz mono to μ-law 8 kHz mono for Twilio outbound media.

    Input: PCM16 little-endian, 16 kHz, mono (e.g. from TTS).
    Output: raw μ-law bytes, 8 kHz; ready for base64 and Twilio media event.

    Real-time friendly: no extra buffering; process and return immediately.
    Empty input returns empty bytes.
    """
    if not pcm16_16k:
        return b""
    pcm16_8k = _resample_16k_to_8k_pure(pcm16_16k)
    return _pcm16_to_ulaw(pcm16_8k)
