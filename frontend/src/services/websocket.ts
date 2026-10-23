import { ClientEventType, ServerEvent, ServerEventType } from '../types/events';

type EventHandler = (event: ServerEvent) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string = '';
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectTimer: number | null = null;

  constructor(defaultUrl?: string) {
    if (defaultUrl) {
      this.url = defaultUrl;
    } else {
      const loc = window.location;
      const host = loc.hostname || 'localhost';
      this.url = `ws://${host}:8000/ws/live`;
    }
  }

  public get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  public connect(customUrl?: string): Promise<void> {
    if (customUrl) {
      this.url = customUrl;
    }

    return new Promise((resolve, reject) => {
      try {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
          this.ws.close();
        }

        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.emit({ type: 'session.ready', payload: { status: 'ws_connected' } });
          resolve();
        };

        this.ws.onmessage = (messageEvent) => {
          try {
            const data: ServerEvent = JSON.parse(messageEvent.data);
            this.emit(data);
          } catch (err) {
            console.error('Failed to parse incoming WebSocket message:', err);
          }
        };

        this.ws.onerror = (err) => {
          console.error('WebSocket connection error:', err);
          this.emit({
            type: 'session.error',
            payload: { code: 'WS_ERROR', message: 'WebSocket connection encountered an error.', recoverable: true }
          });
          reject(err);
        };

        this.ws.onclose = (closeEvent) => {
          this.emit({
            type: 'session.closed',
            payload: { reason: closeEvent.reason || `Code: ${closeEvent.code}` }
          });
          this.ws = null;
        };
      } catch (e) {
        reject(e);
      }
    });
  }

  public send(type: ClientEventType, payload: Record<string, any> = {}): void {
    if (!this.isConnected || !this.ws) {
      console.warn(`Cannot send event ${type}: WebSocket is not open.`);
      return;
    }

    const message = JSON.stringify({ type, payload });
    this.ws.send(message);
  }

  public on(eventType: ServerEventType | '*', handler: EventHandler): () => void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // Return unbind function
    return () => this.off(eventType, handler);
  }

  public off(eventType: ServerEventType | '*', handler: EventHandler): void {
    const set = this.handlers.get(eventType);
    if (set) {
      set.delete(handler);
      if (set.size === 0) {
        this.handlers.delete(eventType);
      }
    }
  }

  private emit(event: ServerEvent): void {
    // Specific handlers
    const specific = this.handlers.get(event.type);
    if (specific) {
      specific.forEach((h) => h(event));
    }
    // Wildcard handlers
    const wildcards = this.handlers.get('*');
    if (wildcards) {
      wildcards.forEach((h) => h(event));
    }
  }

  public disconnect(reason: string = 'user_disconnected'): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.send('session.stop', { reason });
      } catch (_) {}
      this.ws.close(1000, reason);
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketClient();
