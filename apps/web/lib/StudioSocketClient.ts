export type StudioEvent = {
  type: "READY" | "STATUS_UPDATE" | "SUCCESS" | "ERROR";
  message: string;
  request_id?: string;
  preview?: unknown;
};

type Listener = (event: StudioEvent) => void;

/** Local-only transport. The token is sent as the first WS message, never in its URL. */
export class StudioSocketClient {
  private socket: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private ready = false;
  readonly origin: string;

  constructor(apiOrigin: string) {
    const url = new URL(apiOrigin);
    if (!["127.0.0.1", "localhost"].includes(url.hostname) || url.protocol !== "http:") {
      throw new Error("The experimental studio supports only a local HTTP Sonic API.");
    }
    this.origin = url.origin;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private emit(message: StudioEvent): void {
    this.listeners.forEach((listener) => listener(message));
  }

  async connect(token: string): Promise<void> {
    if (!token) throw new Error("Enter the local Sonic operator token.");
    this.disconnect();
    const url = new URL("/workbench/ws/studio", this.origin);
    url.protocol = "ws:";
    const ws = new WebSocket(url.toString());
    this.socket = ws;
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const finish = (error?: Error) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (error) reject(error); else resolve();
      };
      const timer = setTimeout(() => {
        ws.close();
        finish(new Error("Connection timed out. Verify Sonic is running locally."));
      }, 8000);
      ws.onopen = () => ws.send(JSON.stringify({type: "AUTH", token}));
      ws.onmessage = (message) => {
        let event: StudioEvent;
        try { event = JSON.parse(message.data); } catch { return; }
        if (!["READY", "STATUS_UPDATE", "SUCCESS", "ERROR"].includes(event.type) ||
            typeof event.message !== "string") return;
        if (event.type === "READY") {
          this.ready = true;
          finish();
        } else if (event.type === "ERROR" && !this.ready) {
          finish(new Error(event.message));
        }
        this.emit(event);
      };
      ws.onerror = () => finish(new Error("Could not connect to the local Sonic service."));
      ws.onclose = () => {
        const wasReady = this.ready;
        this.ready = false;
        finish(new Error("The local studio connection was closed."));
        if (wasReady) this.emit({type: "ERROR", message: "Studio disconnected. Reconnect to continue."});
      };
    });
  }

  sendPromptToAI(text: string, _currentProjectState: unknown): string {
    if (!this.ready || this.socket?.readyState !== WebSocket.OPEN) {
      throw new Error("Connect to Sonic before sending a prompt.");
    }
    const requestId = crypto.randomUUID();
    // Current project state is intentionally NOT sent or changed: no canonical timeline is wired yet.
    this.socket.send(JSON.stringify({type: "PROMPT", request_id: requestId, text}));
    return requestId;
  }

  disconnect(): void {
    this.ready = false;
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }
  }
}
