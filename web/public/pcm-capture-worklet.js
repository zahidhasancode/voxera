/**
 * Microphone capture worklet.
 *
 * Runs on the audio thread. Receives float samples at the AudioContext's real
 * sample rate, resamples them to the target rate by linear interpolation (the
 * read position and the last input sample carry over between render blocks),
 * converts to PCM16 little-endian and posts fixed-size frames to the main thread.
 *
 * Plain JavaScript on purpose: it is served as-is from /public and loaded with
 * audioWorklet.addModule(), so it must not depend on the bundler.
 *
 * Messages to the main thread:   { type: "frame", pcm: ArrayBuffer, rms: number }
 * Messages from the main thread: { type: "stop" }
 */
class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const opts = (options && options.processorOptions) || {};
    this.targetRate = opts.targetSampleRate || 16000;
    this.frameSamples = opts.frameSamples || 320;

    // Input samples consumed per output sample. `sampleRate` is the worklet global.
    this.step = sampleRate / this.targetRate;
    // Read position in the current block. -1 addresses the last sample of the previous block.
    this.pos = 0;
    this.prev = 0;

    this.frame = new DataView(new ArrayBuffer(this.frameSamples * 2));
    this.filled = 0;
    this.sumSquares = 0;
    this.running = true;

    this.port.onmessage = (ev) => {
      if (ev.data && ev.data.type === "stop") this.running = false;
    };
  }

  emit(sample) {
    const s = sample < -1 ? -1 : sample > 1 ? 1 : sample;
    this.frame.setInt16(this.filled * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    this.sumSquares += s * s;
    this.filled++;

    if (this.filled === this.frameSamples) {
      const pcm = this.frame.buffer;
      const rms = Math.sqrt(this.sumSquares / this.frameSamples);
      this.port.postMessage({ type: "frame", pcm, rms }, [pcm]);
      this.frame = new DataView(new ArrayBuffer(this.frameSamples * 2));
      this.filled = 0;
      this.sumSquares = 0;
    }
  }

  process(inputs) {
    if (!this.running) return false;

    const input = inputs[0] && inputs[0][0];
    if (!input || input.length === 0) return true;

    const n = input.length;
    // Interpolating at `pos` needs samples floor(pos) and floor(pos) + 1.
    while (this.pos < n - 1) {
      const i = Math.floor(this.pos);
      const frac = this.pos - i;
      const a = i < 0 ? this.prev : input[i];
      const b = input[i + 1];
      this.emit(a + (b - a) * frac);
      this.pos += this.step;
    }
    this.pos -= n;
    this.prev = input[n - 1];
    return true;
  }
}

registerProcessor("pcm-capture", PcmCaptureProcessor);
