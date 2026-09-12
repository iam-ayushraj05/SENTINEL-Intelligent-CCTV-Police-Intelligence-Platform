"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Video,
  VideoOff,
  RefreshCw,
  Maximize,
  Camera,
  Download,
  Loader2,
  AlertTriangle,
  Lock,
  Play,
  Pause,
  Wifi,
  WifiOff,
} from "lucide-react";
import { HLSPlayerManager, type PlaybackState, type PlaybackError } from "@/lib/hlsPlayer";
import { cctvApi, type CCTVCameraEntry } from "@/lib/api";
import type { Camera as CameraType } from "@/lib/types";

interface LiveStreamPlayerProps {
  /** Local backend camera */
  camera?: CameraType;
  /** CDN catalogue camera */
  cctvCamera?: CCTVCameraEntry;
  /** Override stream URL */
  streamUrl?: string;
  /** Show AI detection overlays */
  showOverlays?: boolean;
  /** Compact mode (smaller controls) */
  compact?: boolean;
  /** Callback when player state changes */
  onStateChange?: (state: PlaybackState) => void;
}

const STATE_LABELS: Record<PlaybackState, string> = {
  IDLE: "Idle",
  LOADING: "Loading…",
  BUFFERING: "Buffering…",
  LIVE: "Live",
  PAUSED: "Paused",
  ERROR: "Error",
  UNSUPPORTED: "Unsupported",
  ACCESS_DENIED: "Access Denied",
  OFFLINE: "Offline",
};

const STATE_COLORS: Record<PlaybackState, string> = {
  IDLE: "bg-gray-500",
  LOADING: "bg-amber-500 animate-pulse",
  BUFFERING: "bg-amber-500 animate-pulse",
  LIVE: "bg-emerald-500",
  PAUSED: "bg-blue-500",
  ERROR: "bg-red-500",
  UNSUPPORTED: "bg-red-500",
  ACCESS_DENIED: "bg-red-600",
  OFFLINE: "bg-gray-600",
};

export default function LiveStreamPlayer({
  camera,
  cctvCamera,
  streamUrl,
  showOverlays = false,
  compact = false,
  onStateChange,
}: LiveStreamPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<HLSPlayerManager | null>(null);
  const [playbackState, setPlaybackState] = useState<PlaybackState>("IDLE");
  const [error, setError] = useState<PlaybackError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [detections, setDetections] = useState<any[]>([]);
  const [showAIOverlay, setShowAIOverlay] = useState(showOverlays);

  // Determine camera identity
  const cameraId = cctvCamera?.id || camera?.camera_code || camera?.id || "unknown";
  const cameraName = cctvCamera?.name || camera?.name || cameraId;

  // Determine stream URL
  const resolvedUrl = streamUrl || (cctvCamera ? cctvApi.getStreamUrl(cctvCamera.id) : null);

  // ---- HLS Player Lifecycle ----
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !resolvedUrl) return;

    // Create new HLS player
    const hls = new HLSPlayerManager();
    hlsRef.current = hls;

    hls.attach(video, resolvedUrl, (state: PlaybackState, err?: PlaybackError) => {
      setPlaybackState(state);
      setRetryCount(hls.retries);
      if (err) setError(err);
      else if (state === "LIVE" || state === "BUFFERING") setError(null);
      onStateChange?.(state);
    });

    return () => {
      hls.detach();
      hlsRef.current = null;
    };
  }, [resolvedUrl]); // Re-attach when URL changes

  // ---- AI Detection Polling (only for backend cameras) ----
  useEffect(() => {
    if (!camera?.id || !showAIOverlay || playbackState !== "LIVE") return;

    const interval = setInterval(async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
        const res = await fetch(`${API_BASE}/detections?camera_id=${camera.id}&limit=10`);
        if (res.ok) {
          const data = await res.json();
          setDetections(Array.isArray(data) ? data : data.detections || []);
        }
      } catch {
        // Silently ignore detection fetch errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [camera?.id, showAIOverlay, playbackState]);

  // ---- Controls ----
  const handleRetry = useCallback(() => {
    if (!videoRef.current || !resolvedUrl) return;
    const hls = new HLSPlayerManager();
    hlsRef.current?.detach();
    hlsRef.current = hls;
    setError(null);
    setRetryCount(0);
    hls.attach(videoRef.current, resolvedUrl, (state, err) => {
      setPlaybackState(state);
      setRetryCount(hls.retries);
      if (err) setError(err);
      else if (state === "LIVE" || state === "BUFFERING") setError(null);
      onStateChange?.(state);
    });
  }, [resolvedUrl, onStateChange]);

  const handlePlayPause = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play().catch(() => {});
    } else {
      video.pause();
    }
  }, []);

  const handleFullscreen = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      video.requestFullscreen?.();
    }
  }, []);

  const handleSnapshot = useCallback(() => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    const link = document.createElement("a");
    link.download = `sentinel-${cameraId}-${Date.now()}.jpg`;
    link.href = canvas.toDataURL("image/jpeg", 0.92);
    link.click();
  }, [cameraId]);

  // ---- Keyboard ----
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case " ":
        case "Enter":
          e.preventDefault();
          handlePlayPause();
          break;
        case "f":
        case "F":
          e.preventDefault();
          handleFullscreen();
          break;
        case "Escape":
          if (document.fullscreenElement) document.exitFullscreen();
          break;
      }
    },
    [handlePlayPause, handleFullscreen]
  );

  const isLoading = playbackState === "LOADING" || playbackState === "BUFFERING";
  const isError = playbackState === "ERROR" || playbackState === "UNSUPPORTED" || playbackState === "ACCESS_DENIED" || playbackState === "OFFLINE";

  return (
    <div
      className={`relative bg-black rounded-lg overflow-hidden group ${compact ? "aspect-video" : ""}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="region"
      aria-label={`Live stream: ${cameraName}`}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        className="w-full h-full object-contain bg-black"
        autoPlay
        muted
        playsInline
        style={{ minHeight: compact ? "120px" : "200px" }}
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60">
          <div className="text-center text-white">
            <Loader2 className="w-8 h-8 mx-auto animate-spin mb-2" />
            <p className="text-sm">{STATE_LABELS[playbackState]}</p>
          </div>
        </div>
      )}

      {/* Error Overlay */}
      {isError && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center text-white max-w-xs px-4">
            {playbackState === "ACCESS_DENIED" ? (
              <Lock className="w-8 h-8 mx-auto mb-2 text-red-400" />
            ) : (
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-400" />
            )}
            <p className="text-sm font-medium mb-1">{STATE_LABELS[playbackState]}</p>
            <p className="text-xs text-gray-400 mb-3">{error?.message || "Stream unavailable"}</p>
            {error?.recoverable !== false && (
              <button
                onClick={handleRetry}
                className="px-3 py-1.5 bg-accent text-white text-xs rounded hover:bg-accent/80 transition"
                aria-label="Retry connection"
              >
                <RefreshCw className="w-3 h-3 inline mr-1" /> Retry
              </button>
            )}
            {retryCount > 0 && (
              <p className="text-xs text-gray-500 mt-2">Retried {retryCount} times</p>
            )}
          </div>
        </div>
      )}

      {/* AI Detection Overlay */}
      {showAIOverlay && playbackState === "LIVE" && detections.length > 0 && (
        <div className="absolute inset-0 pointer-events-none">
          {detections.map((det, i) => {
            const bbox = det.bbox || {};
            const video = videoRef.current;
            if (!video) return null;
            const scaleX = video.clientWidth / (video.videoWidth || 1);
            const scaleY = video.clientHeight / (video.videoHeight || 1);
            return (
              <div
                key={`det-${i}`}
                className="absolute border-2 border-accent/80 rounded"
                style={{
                  left: (bbox.x1 || 0) * scaleX,
                  top: (bbox.y1 || 0) * scaleY,
                  width: ((bbox.x2 || 0) - (bbox.x1 || 0)) * scaleX,
                  height: ((bbox.y2 || 0) - (bbox.y1 || 0)) * scaleY,
                }}
              >
                <span className="absolute -top-5 left-0 text-[10px] bg-accent/90 text-white px-1 rounded">
                  {det.object_type} {Math.round((det.confidence || 0) * 100)}%
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Status Badge */}
      <div className="absolute top-2 left-2 flex items-center gap-1.5">
        <span className={`w-2 h-2 rounded-full ${STATE_COLORS[playbackState]}`} />
        <span className="text-[10px] text-white/90 font-medium bg-black/50 px-1.5 py-0.5 rounded">
          {compact ? cameraId.toUpperCase() : cameraName}
        </span>
        {playbackState === "LIVE" && (
          <span className="text-[10px] text-emerald-400 font-bold bg-black/50 px-1 py-0.5 rounded flex items-center gap-1">
            <Wifi className="w-2.5 h-2.5" /> LIVE
          </span>
        )}
      </div>

      {/* Controls Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            onClick={handlePlayPause}
            className="p-1 text-white/80 hover:text-white transition"
            aria-label={playbackState === "PAUSED" ? "Play" : "Pause"}
          >
            {playbackState === "PAUSED" ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </button>
          {camera && (
            <button
              onClick={() => setShowAIOverlay(!showAIOverlay)}
              className={`p-1 text-white/80 hover:text-white transition ${showAIOverlay ? "text-accent" : ""}`}
              aria-label="Toggle AI overlays"
            >
              <Camera className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleSnapshot}
            className="p-1 text-white/80 hover:text-white transition"
            aria-label="Take snapshot"
            disabled={playbackState !== "LIVE"}
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleRetry}
            className="p-1 text-white/80 hover:text-white transition"
            aria-label="Retry stream"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleFullscreen}
            className="p-1 text-white/80 hover:text-white transition"
            aria-label="Fullscreen"
          >
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
