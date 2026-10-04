export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "error";

export interface WebSocketMessage {
  type: string;
  payload?: Record<string, unknown>;
  timestamp?: string;
}

type MessageHandler = (message: WebSocketMessage) => void;
type StatusHandler = (status: WebSocketStatus) => void;

function wsUrl(): string {
  const env = import.meta.env.VITE_WS_URL;
  if (env) return env;
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/api/v1/ws/operations`;
}

export class OperationsWebSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<MessageHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private token: string | null = null;

  connect(token?: string) {
    this.token = token ?? null;
    this.shouldReconnect = true;
    this.open();
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.emitStatus("disconnected");
  }

  subscribe(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  onStatus(handler: StatusHandler) {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  send(message: WebSocketMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private open() {
    this.emitStatus("connecting");
    const url = this.token ? `${wsUrl()}?token=${encodeURIComponent(this.token)}` : wsUrl();

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.emitStatus("error");
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => this.emitStatus("connected");

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as WebSocketMessage;
        this.handlers.forEach((h) => h(data));
      } catch {
        /* ignore malformed frames */
      }
    };

    this.ws.onerror = () => this.emitStatus("error");

    this.ws.onclose = () => {
      this.emitStatus("disconnected");
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect) return;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.open(), 3000);
  }

  private emitStatus(status: WebSocketStatus) {
    this.statusHandlers.forEach((h) => h(status));
  }
}

export const operationsSocket = new OperationsWebSocket();
