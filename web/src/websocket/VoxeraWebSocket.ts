/**
 * Central WebSocket service for Voxera backend.
 * Typed event handling, reconnection, and binary frame routing.
 */

const WS_URL =
  import.meta.env.VITE_WS_URL ||
  (() => {
    const { protocol, host } = window.location;
    const wsProto = protocol === "https:" ? "wss:" : "ws:";
    return `${wsProto}//${host}/api/v1/`;
  })();

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
    this.ws = new WebSocket(this.url);
    this.ws.binaryType = "arraybuffer";

    this.ws.onopen = () => {
      this._connecting = false;
      this._connected = true;
      this.onJson({ type: "connection", status: "connected" });
    };

    this.ws.onmessage = (ev: MessageEvent) => {
      if (typeof ev.data === "string") {
        try {
          const d = JSON.parse(ev.data);
          this.onJson(d);
        } catch {
          this.onJson({ type: "unknown", raw: ev.data });
        }
      } else if (ev.data instanceof ArrayBuffer) {
        this.onBinary(ev.data);
      }
    };

    this.ws.onclose = () => {
      this._connecting = false;
      this._connected = false;
      this.ws = null;
      this.onJson({ type: "connection", status: "disconnected" });
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  disconnect(): void {
    this._connecting = false;
    this._connected = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
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
}
