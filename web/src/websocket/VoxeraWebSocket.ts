/**
 * Central WebSocket service for Voxera backend.
 * Text messages are parsed as JSON and passed to onJson; binary messages
 * (PCM16 audio) are passed to onBinary untouched.
 */

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  (() => {
    const { protocol, host } = window.location;
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    return `${wsProto}//${host}/api/v1/`;
  })();

/** Mic frames are real-time: once this much is waiting to be sent, new frames are dropped. */
const MAX_BUFFERED_BYTES = 32000; // 1 s of PCM16 mono 16 kHz

export type JsonHandler = (data: unknown) => void;
export type BinaryHandler = (data: ArrayBuffer) => void;

export class VoxeraWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private onJson: JsonHandler;
  private onBinary: BinaryHandler;
  private _connecting = false;
  private _connected = false;

  constructor(onJson: JsonHandler, onBinary: BinaryHandler, url = WS_URL) {
    this.url = url;
    this.onJson = onJson;
    this.onBinary = onBinary;
  }

  get connecting(): boolean {
    return this._connecting;
  }

  get connected(): boolean {
    return this._connected && this.ws?.readyState === WebSocket.OPEN;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this._connecting) return;
    this._connecting = true;
    const ws = new WebSocket(this.url);
    ws.binaryType = "arraybuffer";
    this.ws = ws;

    ws.onopen = () => {
      this._connecting = false;
      this._connected = true;
      this.onJson({ type: "connection", status: "connected" });
    };

    ws.onmessage = (ev: MessageEvent) => {
      if (typeof ev.data === "string") {
        let parsed: unknown;
        try {
          parsed = JSON.parse(ev.data);
        } catch {
          return; // not JSON: ignore
        }
        this.onJson(parsed);
      } else if (ev.data instanceof ArrayBuffer) {
        this.onBinary(ev.data);
      }
    };

    ws.onclose = () => {
      this._connecting = false;
      this._connected = false;
      this.ws = null;
      this.onJson({ type: "connection", status: "disconnected" });
    };

    ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  disconnect(): void {
    this._connecting = false;
    this._connected = false;
    const ws = this.ws;
    this.ws = null;
    if (ws) {
      // Detach first: a late close event must not reach a newer session.
      ws.onopen = null;
      ws.onmessage = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.close();
    }
  }

  send(data: string | object): void {
    if (!this.connected || !this.ws) return;
    const s = typeof data === "string" ? data : JSON.stringify(data);
    this.ws.send(s);
  }

  sendJson(obj: object): void {
    this.send(obj);
  }

  /** Send one binary message. Returns false if it was not sent (closed or backed up). */
  sendBinary(data: ArrayBuffer): boolean {
    if (!this.connected || !this.ws) return false;
    if (this.ws.bufferedAmount > MAX_BUFFERED_BYTES) return false;
    this.ws.send(data);
    return true;
  }
}
