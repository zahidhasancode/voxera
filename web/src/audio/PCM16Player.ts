/**
 * PCM16 mono 16kHz → Web Audio API playback.
 * Buffers 20ms frames (640 bytes) and plays with minimal latency.
 */

const SAMPLE_RATE = 16000;
const BYTES_PER_SAMPLE = 2;

export type PlaybackState = "idle" | "playing";

export interface PCM16PlayerCallbacks {
  onStateChange?: (state: PlaybackState) => void;
  onFramePlayed?: (count: number) => void;
}

export class PCM16Player {
  private ctx: AudioContext | null = null;
  private scheduled = 0;
  private nextStart = 0;
  private callbacks: PCM16PlayerCallbacks;
  private _frameCount = 0;

  constructor(callbacks: PCM16PlayerCallbacks = {}) {
    this.callbacks = callbacks;
  }

  get frameCount(): number {
    return this._frameCount;
  }

  async init(): Promise<void> {
    if (this.ctx?.state === "running") return;
    this.ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)({
      sampleRate: SAMPLE_RATE,
    });
    if (this.ctx.state !== "running") {
      await this.ctx.resume();
    }
    this.nextStart = this.ctx.currentTime;
    this.scheduled = 0;
    this._frameCount = 0;
    this.callbacks.onStateChange?.("idle");
  }

  playChunk(pcm16: ArrayBuffer): void {
    if (!this.ctx || this.ctx.state !== "running") return;

    const buf = this.ctx.createBuffer(1, pcm16.byteLength / BYTES_PER_SAMPLE, SAMPLE_RATE);
    const ch = buf.getChannelData(0);
    const view = new Int16Array(pcm16);
    for (let i = 0; i < ch.length; i++) {
      ch[i] = view[i] / 32768;
    }

    const start = Math.max(this.ctx.currentTime, this.nextStart);
    const duration = buf.duration;
    this.nextStart = start + duration;

    const src = this.ctx.createBufferSource();
    src.buffer = buf;
    src.connect(this.ctx.destination);
    src.start(start);
    src.stop(start + duration);
    src.onended = () => {
      this.scheduled--;
      this._frameCount++;
      this.callbacks.onFramePlayed?.(this._frameCount);
      if (this.scheduled <= 0) {
        this.callbacks.onStateChange?.("idle");
      }
    };

    this.scheduled++;
    this.callbacks.onStateChange?.("playing");
  }

  /** Push raw PCM16 bytes (e.g. 640-byte 20ms frame). */
  push(pcm16: ArrayBuffer): void {
    this.init().then(() => this.playChunk(pcm16));
  }

  reset(): void {
    this.nextStart = this.ctx?.currentTime ?? 0;
    this._frameCount = 0;
    this.callbacks.onStateChange?.("idle");
  }

  async close(): Promise<void> {
    if (this.ctx) {
      await this.ctx.close();
      this.ctx = null;
    }
    this.scheduled = 0;
    this.callbacks.onStateChange?.("idle");
  }
}
