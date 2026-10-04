/**
 * Microphone → PCM16 mono 16 kHz, 20 ms frames (640 bytes).
 *
 * getUserMedia feeds an AudioWorklet (public/pcm-capture-worklet.js) that
 * resamples from the AudioContext's real rate and posts ready-to-send frames.
 */

import { FRAME_BYTES, FRAME_SAMPLES, SAMPLE_RATE } from "./format";

const WORKLET_URL = `${import.meta.env.BASE_URL}pcm-capture-worklet.js`;
const WORKLET_NAME = "pcm-capture";
/** Gentle low-pass ahead of the resampler; linear interpolation alone does not band-limit. */
const ANTI_ALIAS_HZ = 7000;

export interface MicCaptureCallbacks {
  /** One 640-byte PCM16 LE frame. */
  onFrame: (pcm: ArrayBuffer) => void;
  /** RMS of the frame, 0..1. */
  onLevel?: (rms: number) => void;
  /** The capture stopped on its own (device unplugged, permission revoked). */
  onEnded?: (reason: string) => void;
}

interface WorkletFrameMessage {
  type: "frame";
  pcm: ArrayBuffer;
  rms: number;
}

function describeError(err: unknown): string {
  if (err instanceof DOMException) {
    switch (err.name) {
      case "NotAllowedError":
      case "SecurityError":
        return "Microphone permission denied. Allow microphone access for this page to use voice.";
      case "NotFoundError":
      case "OverconstrainedError":
        return "No usable microphone was found.";
      case "NotReadableError":
        return "The microphone is in use by another application or could not be opened.";
      default:
        return `Microphone error: ${err.message || err.name}`;
    }
  }
  return `Microphone error: ${err instanceof Error ? err.message : String(err)}`;
}

export class MicCapture {
  private callbacks: MicCaptureCallbacks;
  private stream: MediaStream | null = null;
  private ctx: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private filter: BiquadFilterNode | null = null;
  private node: AudioWorkletNode | null = null;
  private sink: GainNode | null = null;
  /** Bumped by stop(); a start() that was overtaken tears itself down. */
  private generation = 0;

  constructor(callbacks: MicCaptureCallbacks) {
    this.callbacks = callbacks;
  }

  get active(): boolean {
    return this.node !== null;
  }

  /** Resolves once frames are flowing. Rejects with a user-readable Error. */
  async start(): Promise<void> {
    if (this.stream) return;
    const generation = ++this.generation;

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Microphone access needs a secure page (https or localhost).");
    }
    if (typeof AudioWorkletNode === "undefined") {
      throw new Error("This browser does not support AudioWorklet.");
    }

    let stream: MediaStream | null = null;
    let ctx: AudioContext | null = null;
    // Nothing is stored on `this` until the graph is complete, so a stop() or a
    // second start() during the awaits below cannot be overwritten by this one.
    const abandon = async (): Promise<void> => {
      stream?.getTracks().forEach((t) => t.stop());
      if (ctx && ctx.state !== "closed") await ctx.close().catch(() => undefined);
    };

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });
      if (generation !== this.generation) return abandon();

      // Default sample rate: the device's own rate. The worklet resamples to 16 kHz.
      ctx = new AudioContext();
      await ctx.audioWorklet.addModule(WORKLET_URL);
      if (ctx.state !== "running") await ctx.resume();
      if (generation !== this.generation) return abandon();

      const source = ctx.createMediaStreamSource(stream);
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = Math.min(ANTI_ALIAS_HZ, ctx.sampleRate / 2);
      filter.Q.value = Math.SQRT1_2;

      const node = new AudioWorkletNode(ctx, WORKLET_NAME, {
        numberOfInputs: 1,
        numberOfOutputs: 1,
        channelCount: 1,
        channelCountMode: "explicit",
        channelInterpretation: "speakers",
        processorOptions: { targetSampleRate: SAMPLE_RATE, frameSamples: FRAME_SAMPLES },
      });
      node.port.onmessage = (ev: MessageEvent<WorkletFrameMessage>) => {
        const msg = ev.data;
        if (msg?.type !== "frame" || msg.pcm.byteLength !== FRAME_BYTES) return;
        this.callbacks.onFrame(msg.pcm);
        this.callbacks.onLevel?.(msg.rms);
      };
      node.onprocessorerror = () => {
        this.callbacks.onEnded?.("The microphone audio processor failed.");
        void this.stop();
      };

      // The worklet writes no output; the muted sink only keeps the graph pulled.
      const sink = ctx.createGain();
      sink.gain.value = 0;
      source.connect(filter).connect(node).connect(sink).connect(ctx.destination);

      for (const track of stream.getAudioTracks()) {
        track.addEventListener("ended", this.handleTrackEnded);
      }

      this.stream = stream;
      this.ctx = ctx;
      this.source = source;
      this.filter = filter;
      this.node = node;
      this.sink = sink;
    } catch (err) {
      await abandon();
      throw new Error(describeError(err));
    }
  }

  async stop(): Promise<void> {
    this.generation++;
    await this.teardown();
  }

  private handleTrackEnded = (): void => {
    if (!this.stream) return;
    this.callbacks.onEnded?.("The microphone was disconnected.");
    void this.stop();
  };

  private async teardown(): Promise<void> {
    const { stream, ctx, source, filter, node, sink } = this;
    this.stream = null;
    this.ctx = null;
    this.source = null;
    this.filter = null;
    this.node = null;
    this.sink = null;

    if (node) {
      node.port.onmessage = null;
      node.onprocessorerror = null;
      node.port.postMessage({ type: "stop" });
    }
    source?.disconnect();
    filter?.disconnect();
    node?.disconnect();
    sink?.disconnect();

    if (stream) {
      for (const track of stream.getTracks()) {
        track.removeEventListener("ended", this.handleTrackEnded);
        track.stop();
      }
    }
    if (ctx && ctx.state !== "closed") {
      try {
        await ctx.close();
      } catch {
        // already closing
      }
    }
  }
}
