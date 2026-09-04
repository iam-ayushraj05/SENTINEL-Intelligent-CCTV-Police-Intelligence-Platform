import { Alert } from "./types";

export type ConnectionStatus = "CONNECTED" | "RECONNECTING" | "OFFLINE";
type AlertCallback = (alert: Alert) => void;
type EventCallback = (eventData: any) => void;
type StatusCallback = (status: ConnectionStatus) => void;

class WebSocketClient {
  private alertWs: WebSocket | null = null;
  private eventWs: WebSocket | null = null;
  private alertCallbacks: AlertCallback[] = [];
  private eventCallbacks: EventCallback[] = [];
  private statusCallbacks: StatusCallback[] = [];
  private isConnectingAlert = false;
  private isConnectingEvent = false;
  private status: ConnectionStatus = "OFFLINE";
  private reconnectDelay = 1000;
  private maxReconnectDelay = 10000;
  private pingInterval: any = null;

  public getStatus(): ConnectionStatus {
    return this.status;
  }

  public subscribeStatus(callback: StatusCallback) {
    this.statusCallbacks.push(callback);
    callback(this.status);
    return () => {
      this.statusCallbacks = this.statusCallbacks.filter((cb) => cb !== callback);
    };
  }

  private setStatus(newStatus: ConnectionStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.statusCallbacks.forEach((cb) => cb(newStatus));
    }
  }

  public subscribeAlerts(callback: AlertCallback) {
    this.alertCallbacks.push(callback);
    this.ensureAlertConnection();
    return () => {
      this.alertCallbacks = this.alertCallbacks.filter((cb) => cb !== callback);
    };
  }

  public subscribeEvents(callback: EventCallback) {
    this.eventCallbacks.push(callback);
    this.ensureEventConnection();
    return () => {
      this.eventCallbacks = this.eventCallbacks.filter((cb) => cb !== callback);
    };
  }

  private getWsBaseUrl(): string {
    const envWs = process.env.NEXT_PUBLIC_WS_URL;
    if (envWs) {
      // Strips trailing slashes or subpaths if provided as base
      const clean = envWs.replace(/\/+$/, "");
      if (clean.includes("/api/v1/ws")) {
        return clean;
      }
      return clean;
    }
    return "ws://localhost:8000";
  }

  private ensureAlertConnection() {
    if (this.alertWs || this.isConnectingAlert) return;
    this.isConnectingAlert = true;
    this.setStatus("RECONNECTING");

    try {
      const baseUrl = this.getWsBaseUrl();
      const wsUrl = baseUrl.endsWith("/alerts")
        ? baseUrl
        : `${baseUrl}/api/v1/ws/alerts`;

      this.alertWs = new WebSocket(wsUrl);

      this.alertWs.onopen = () => {
        this.isConnectingAlert = false;
        this.setStatus("CONNECTED");
        this.reconnectDelay = 1000;
        console.log(`[Sentinel WS] Connected to Alert Stream: ${wsUrl}`);
        
        // Start ping heartbeat
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = setInterval(() => {
          if (this.alertWs && this.alertWs.readyState === WebSocket.OPEN) {
            this.alertWs.send("ping");
          }
        }, 15000);
      };

      this.alertWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") return; // Keep-alive response

          if ((data.type === "ALERT_CREATED" || data.event === "ALERT_CREATED") && data.alert) {
            this.alertCallbacks.forEach((cb) => cb(data.alert));
          } else if (data.alert_code || data.id) {
            // Direct alert object broadcast
            this.alertCallbacks.forEach((cb) => cb(data));
          }
        } catch (e) {
          console.error("[Sentinel WS] Error parsing alert frame:", e);
        }
      };

      this.alertWs.onclose = () => {
        this.alertWs = null;
        this.isConnectingAlert = false;
        this.setStatus("RECONNECTING");
        if (this.pingInterval) clearInterval(this.pingInterval);

        // Exponential backoff reconnect
        setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
          this.ensureAlertConnection();
        }, this.reconnectDelay);
      };

      this.alertWs.onerror = (err) => {
        console.warn("[Sentinel WS] Alert stream error:", err);
        if (this.alertWs) this.alertWs.close();
      };
    } catch {
      this.isConnectingAlert = false;
      this.setStatus("OFFLINE");
    }
  }

  private ensureEventConnection() {
    if (this.eventWs || this.isConnectingEvent) return;
    this.isConnectingEvent = true;

    try {
      const baseUrl = this.getWsBaseUrl();
      const wsUrl = baseUrl.endsWith("/events")
        ? baseUrl
        : `${baseUrl}/api/v1/ws/events`;

      this.eventWs = new WebSocket(wsUrl);

      this.eventWs.onopen = () => {
        this.isConnectingEvent = false;
        console.log(`[Sentinel WS] Connected to Event Stream: ${wsUrl}`);
      };

      this.eventWs.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") return;
          if (data.type === "AI_EVENT" && data.event) {
            this.eventCallbacks.forEach((cb) => cb(data.event));
          }
        } catch (e) {
          console.error("[Sentinel WS] Error parsing event frame:", e);
        }
      };

      this.eventWs.onclose = () => {
        this.eventWs = null;
        this.isConnectingEvent = false;
        setTimeout(() => this.ensureEventConnection(), 5000);
      };

      this.eventWs.onerror = () => {
        if (this.eventWs) this.eventWs.close();
      };
    } catch {
      this.isConnectingEvent = false;
    }
  }
}

export const wsClient = new WebSocketClient();
