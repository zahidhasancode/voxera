/** Wire audio format, both directions: PCM16 little-endian, mono, 16 kHz, 20 ms frames. */

export const SAMPLE_RATE = 16000;
export const FRAME_MS = 20;
export const BYTES_PER_SAMPLE = 2;
export const FRAME_SAMPLES = (SAMPLE_RATE * FRAME_MS) / 1000;
export const FRAME_BYTES = FRAME_SAMPLES * BYTES_PER_SAMPLE;
export const ENCODING = "pcm_s16le";
