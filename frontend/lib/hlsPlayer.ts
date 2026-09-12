/**
 * HLS Player Engine — manages hls.js / native HLS playback lifecycle.
 *
 * Features:
 * - Native HLS detection (Safari) with hls.js fallback (Chrome/Firefox/Edge)
 * - Lifecycle: attach(video, url) → detach() with full cleanup
 * - Exponential backoff reconnect: 2→4→8→16→30s cap, ±25% jitter
 * - Fatal vs non-fatal error recovery
 * - State callbacks for UI updates
 * - No tight loops — retry counter + backoff cap
 */

import Hls, { type ErrorData, type HlsConfig } from "hls.js";

export type PlaybackState =
  | "IDLE"
  | "LOADING"
  | "BUFFERING"
  | "LIVE"
  | "PAUSED"
  | "ERROR"
  | "UNSUPPORTED"
  | "ACCESS_DENIED"
  | "OFFLINE";

export interface PlaybackError {
  state: PlaybackState;
  message: string;
  recoverable: boolean;
}

export type StateCallback = (state: PlaybackState, error?: PlaybackError) => void;

interface BackoffConfig {
  initialDelay: number;
  maxDelay: number;
  jitter: number;
  maxRetries: number;
  stableThreshold: number; // seconds of stable playback before reset
}

const DEFAULT_BACKOFF: BackoffConfig = {
  initialDelay: 2000,
  maxDelay: 30000,
  jitter: 0.25,
  maxRetries: 20,
  stableThreshold: 10,
};

export class HLSPlayerManager {
  private hls: Hls | null = null;
  private video: HTMLVideoElement | null = null;
  private url: string | null = null;
  private onStateChange: StateCallback | null = null;
  private currentState: PlaybackState = "IDLE";
  private retryCount = 0;
  private currentDelay: number;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private stableTimer: ReturnType<typeof setTimeout> | null = null;
  private isNativeHLS = false;
  private destroyed = false;
  private config: BackoffConfig;

  constructor(config?: Partial<BackoffConfig>) {
    this.config = { ...DEFAULT_BACKOFF, ...config };
    this.currentDelay = this.config.initialDelay;
  }

  /**
   * Check if the browser supports native HLS (Safari).
   */
  static supportsNativeHLS(): boolean {
    if (typeof document === "undefined") return false;
    const video = document.createElement("video");
    return video.canPlayType("application/vnd.apple.mpegurl") !== "";
  }

  /**
   * Attach to a video element and start loading the HLS stream.
   */
  attach(video: HTMLVideoElement, url: string, onStateChange?: StateCallback): void {
    // Cleanup any previous attachment
    this.detach();

    this.video = video;
    this.url = url;
    this.onStateChange = onStateChange || null;
    this.destroyed = false;
    this.retryCount = 0;
    this.currentDelay = this.config.initialDelay;

    this.setState("LOADING");

    if (HLSPlayerManager.supportsNativeHLS()) {
      this.attachNative(video, url);
    } else if (Hls.isSupported()) {
      this.attachHlsJs(video, url);
    } else {
      this.setState("UNSUPPORTED", {
        state: "UNSUPPORTED",
        message: "HLS is not supported in this browser",
        recoverable: false,
      });
    }
  }

  /**
   * Detach from the video element and clean up all resources.
   */
  detach(): void {
    this.destroyed = true;
    this.clearTimers();

    if (this.hls) {
      this.hls.destroy();
      this.hls = null;
    }

    if (this.video) {
      this.video.removeAttribute("src");
      this.video.load(); // Reset the video element
      this.video = null;
    }

    this.url = null;
    this.isNativeHLS = false;
    this.setState("IDLE");
    this.onStateChange = null;
  }

  get state(): PlaybackState {
    return this.currentState;
  }

  get retries(): number {
    return this.retryCount;
  }

  // ---------- Native HLS (Safari) ----------

  private attachNative(video: HTMLVideoElement, url: string): void {
    this.isNativeHLS = true;

    const onPlaying = () => {
      this.setState("LIVE");
      this.startStableTimer();
    };
    const onWaiting = () => {
      if (this.currentState === "LIVE") this.setState("BUFFERING");
    };
    const onPause = () => {
      if (!this.destroyed) this.setState("PAUSED");
    };
    const onError = () => {
      const err = video.error;
      this.setState("ERROR", {
        state: "ERROR",
        message: err?.message || "Native HLS playback error",
        recoverable: true,
      });
      this.scheduleRetry();
    };

    video.addEventListener("playing", onPlaying);
    video.addEventListener("waiting", onWaiting);
    video.addEventListener("pause", onPause);
    video.addEventListener("error", onError);

    video.src = url;
    video.load();

    if (video.autoplay) {
      video.play().catch(() => {
        // Autoplay blocked — user needs to interact
        this.setState("PAUSED");
      });
    }
  }

  // ---------- hls.js (Chrome/Firefox/Edge) ----------

  private attachHlsJs(video: HTMLVideoElement, url: string): void {
    const hlsConfig: Partial<HlsConfig> = {
      enableWorker: true,
      lowLatencyMode: true,
      backBufferLength: 30,
      maxBufferLength: 10,
      maxMaxBufferLength: 30,
      startFragPrefetch: true,
    };

    this.hls = new Hls(hlsConfig);

    this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
      this.setState("BUFFERING");
      video.play().catch(() => {
        this.setState("PAUSED");
      });
    });

    this.hls.on(Hls.Events.FRAG_LOADED, () => {
      if (this.currentState === "LOADING") {
        this.setState("BUFFERING");
      }
    });

    this.hls.on(Hls.Events.ERROR, (_event, data: ErrorData) => {
      if (!data.fatal) return;

      switch (data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
          if (data.response && (data.response.code === 401 || data.response.code === 403)) {
            this.setState("ACCESS_DENIED", {
              state: "ACCESS_DENIED",
              message: "Stream access denied — authentication failed",
              recoverable: false,
            });
          } else {
            this.setState("ERROR", {
              state: "ERROR",
              message: `Network error: ${data.details}`,
              recoverable: true,
            });
            this.scheduleRetry();
          }
          break;

        case Hls.ErrorTypes.MEDIA_ERROR:
          // Try media error recovery first
          this.hls?.recoverMediaError();
          break;

        default:
          this.setState("ERROR", {
            state: "ERROR",
            message: `Fatal error: ${data.details}`,
            recoverable: false,
          });
          break;
      }
    });

    // Track playback state via video events
    video.addEventListener("playing", () => {
      this.setState("LIVE");
      this.startStableTimer();
    });

    video.addEventListener("waiting", () => {
      if (this.currentState === "LIVE") this.setState("BUFFERING");
    });

    video.addEventListener("pause", () => {
      if (!this.destroyed) this.setState("PAUSED");
    });

    this.hls.loadSource(url);
    this.hls.attachMedia(video);
  }

  // ---------- Retry Logic ----------

  private scheduleRetry(): void {
    if (this.destroyed) return;
    if (this.config.maxRetries > 0 && this.retryCount >= this.config.maxRetries) {
      this.setState("OFFLINE", {
        state: "OFFLINE",
        message: "Maximum retry attempts exceeded",
        recoverable: false,
      });
      return;
    }

    this.clearTimers();

    // Calculate delay with jitter
    const jitter = 1 + (Math.random() * 2 - 1) * this.config.jitter;
    const delay = Math.min(this.currentDelay * jitter, this.config.maxDelay);

    this.retryTimer = setTimeout(() => {
      if (this.destroyed || !this.video || !this.url) return;

      this.retryCount++;
      this.currentDelay = Math.min(this.currentDelay * 2, this.config.maxDelay);
      this.setState("LOADING");

      // Re-attach
      if (this.hls) {
        this.hls.destroy();
        this.hls = null;
      }

      if (this.isNativeHLS) {
        this.attachNative(this.video!, this.url!);
      } else {
        this.attachHlsJs(this.video!, this.url!);
      }
    }, delay);
  }

  private startStableTimer(): void {
    this.clearStableTimer();
    this.stableTimer = setTimeout(() => {
      // Stream has been stable — reset backoff
      this.retryCount = 0;
      this.currentDelay = this.config.initialDelay;
    }, this.config.stableThreshold * 1000);
  }

  // ---------- State Management ----------

  private setState(state: PlaybackState, error?: PlaybackError): void {
    if (this.currentState === state) return;
    this.currentState = state;
    this.onStateChange?.(state, error);
  }

  // ---------- Cleanup ----------

  private clearTimers(): void {
    this.clearRetryTimer();
    this.clearStableTimer();
  }

  private clearRetryTimer(): void {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
  }

  private clearStableTimer(): void {
    if (this.stableTimer) {
      clearTimeout(this.stableTimer);
      this.stableTimer = null;
    }
  }
}
