/**
 * PCM16 LE mono 16 kHz → Web Audio API playback.
 *
 * Each incoming chunk becomes an AudioBufferSourceNode scheduled at a running
 * `nextStartTime`, so consecutive chunks play back to back. When the queue is
 * empty (start of a reply, or after an underrun) playback is delayed by a short
 * jitter buffer. clear() stops every scheduled source at once (barge-in).
 */

import { BYTES_PER_SAMPLE, SAMPLE_RATE } from "./format";

/** Lead time before the first chunk of a burst plays, to absorb network jitter. */
const JITTER_BUFFER_S = 0.08;

export type PlaybackState = "idle" | "playing";

export interface PCM16PlayerCallbacks {
  onStateChange?: (state: PlaybackState) => void;
  /**
   * The first audio after beginStream() has started playing. `heardAtMs` is on the
   * performance.now() clock and includes the output latency the browser reports,
   * where it reports one.
   */
  onFirstAudio?: (heardAtMs: number) => void;
}

type AudioContextCtor = typeof AudioContext;

export class PCM16Player {
  private ctx: AudioContext | null = null;
  private initPromise: Promise<void> | null = null;
  private sources = new Set<AudioBufferSourceNode>();
  /** Chunks received while the AudioContext was not running. */
  private pending: ArrayBuffer[] = [];
  /** Odd trailing byte of a chunk that did not end on a sample boundary. */
  private carry: number | null = null;
  private nextStartTime = 0;
  private state: PlaybackState = "idle";
  private awaitingFirstAudio = false;
  private firstAudioTimer: ReturnType<typeof setTimeout> | null = null;
  private callbacks: PCM16PlayerCallbacks;
  private _frameCount = 0;
  private closed = false;

  constructor(callbacks: PCM16PlayerCallbacks = {}) {
    this.callbacks = callbacks;
  }

  /** Chunks that finished playing since the last reset. */
  get frameCount(): number {
    return this._frameCount;
  }

  get playing(): boolean {
    return this.state === "playing";
  }

  /** Create and resume the AudioContext. Call from a user gesture. */
  init(): Promise<void> {
    if (!this.initPromise) {
      this.initPromise = this.open().catch((err) => {
        this.initPromise = null;
        throw err;
      });
    }
    return this.initPromise;
  }

  private async open(): Promise<void> {
    if (this.closed) return;
    const Ctor: AudioContextCtor =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: AudioContextCtor }).webkitAudioContext;
    // A 16 kHz context plays the buffers without resampling each chunk. A browser
    // that refuses that rate gets its default one and resamples the 16 kHz buffers.
    let ctx: AudioContext;
    try {
      ctx = new Ctor({ sampleRate: SAMPLE_RATE, latencyHint: "interactive" });
    } catch {
      ctx = new Ctor({ latencyHint: "interactive" });
    }
    this.ctx = ctx;
    if (ctx.state !== "running") await ctx.resume();
    if (this.closed || this.ctx !== ctx) return;
    this.flushPending();
  }

  /** Mark the start of a TTS stream; the next chunk scheduled reports onFirstAudio. */
  beginStream(): void {
    this.carry = null;
    // A report already on its way belongs to audio that is about to play; keep it.
    if (!this.firstAudioTimer) this.awaitingFirstAudio = true;
  }

  /** Queue raw PCM16 LE bytes (normally one 640-byte, 20 ms frame). */
  push(pcm16: ArrayBuffer): void {
    if (this.closed || pcm16.byteLength === 0) return;
    if (this.ctx?.state === "running") {
      this.schedule(pcm16);
      return;
    }
    this.pending.push(pcm16);
    this.ensureRunning().catch(() => {
      // Playback is unavailable (autoplay policy or no audio device); drop the audio.
      this.pending = [];
    });
  }

  /** Stop everything that is playing or scheduled and drop all queued audio. */
  clear(): void {
    this.pending = [];
    this.carry = null;
    this.awaitingFirstAudio = false;
    if (this.firstAudioTimer) {
      clearTimeout(this.firstAudioTimer);
      this.firstAudioTimer = null;
    }

    const sources = [...this.sources];
    this.sources.clear();
    for (const src of sources) {
      src.onended = null;
      try {
        src.stop();
      } catch {
        // already stopped
      }
      src.disconnect();
    }
    this.nextStartTime = 0;
    this.setState("idle");
  }

  /** clear() and zero the played-chunk counter. */
  reset(): void {
    this.clear();
    this._frameCount = 0;
  }

  async close(): Promise<void> {
    this.closed = true;
    this.clear();
    const ctx = this.ctx;
    this.ctx = null;
    this.initPromise = null;
    if (ctx && ctx.state !== "closed") {
      try {
        await ctx.close();
      } catch {
        // already closing
      }
    }
  }

  private async ensureRunning(): Promise<void> {
    const ctx = this.ctx;
    if (!ctx) return this.init();
    await ctx.resume();
    if (this.ctx === ctx) this.flushPending();
  }

  private flushPending(): void {
    const chunks = this.pending;
    this.pending = [];
    for (const chunk of chunks) this.schedule(chunk);
  }

  private schedule(pcm16: ArrayBuffer): void {
    const ctx = this.ctx;
    if (!ctx) return;

    const samples = this.decode(pcm16);
    if (samples.length === 0) return;

    const buf = ctx.createBuffer(1, samples.length, SAMPLE_RATE);
    buf.getChannelData(0).set(samples);

    const now = ctx.currentTime;
    // The queue ran dry (or this is the first chunk): rebuild the jitter buffer.
    if (this.nextStartTime < now) this.nextStartTime = now + JITTER_BUFFER_S;
    const start = this.nextStartTime;
    this.nextStartTime = start + buf.duration;

    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    src.onended = () => {
      src.disconnect();
      if (!this.sources.delete(src)) return;
      this._frameCount++;
      if (this.sources.size === 0) this.setState("idle");
    };
    this.sources.add(src);
    src.start(start);
    this.setState("playing");

    if (this.awaitingFirstAudio) {
      this.awaitingFirstAudio = false;
      const outputLatencyS = ctx.outputLatency || ctx.baseLatency || 0;
      const delayMs = (start - now + outputLatencyS) * 1000;
      const heardAtMs = performance.now() + delayMs;
      // Reported when the audio is due, so a clear() before then cancels it.
      this.firstAudioTimer = setTimeout(() => {
        this.firstAudioTimer = null;
        this.callbacks.onFirstAudio?.(heardAtMs);
      }, delayMs);
    }
  }

  /** PCM16 LE bytes → float samples, carrying an odd trailing byte to the next chunk. */
  private decode(pcm16: ArrayBuffer): Float32Array {
    let bytes = new Uint8Array(pcm16);
    if (this.carry !== null) {
      const joined = new Uint8Array(bytes.length + 1);
      joined[0] = this.carry;
      joined.set(bytes, 1);
      bytes = joined;
      this.carry = null;
    }
    if (bytes.length % BYTES_PER_SAMPLE !== 0) {
      this.carry = bytes[bytes.length - 1];
      bytes = bytes.subarray(0, bytes.length - 1);
    }

    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const out = new Float32Array(bytes.length / BYTES_PER_SAMPLE);
    for (let i = 0; i < out.length; i++) {
      out[i] = view.getInt16(i * BYTES_PER_SAMPLE, true) / 32768;
    }
    return out;
  }

  private setState(state: PlaybackState): void {
    if (this.state === state) return;
    this.state = state;
    this.callbacks.onStateChange?.(state);
  }
}
