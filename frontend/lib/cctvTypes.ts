/**
 * Types for the cctv.corp8.cloud camera catalogue and HLS playback.
 *
 * The endpoint is protected, so this remains a runtime-validated flexible
 * shape until an authorized response is available.
 */

// ---------------------------------------------------------------------------
// Camera Catalogue
// ---------------------------------------------------------------------------

/** A single camera entry from the CDN catalogue. */
export interface CCTVCamera {
  /** Camera identifier, e.g. "cam01" */
  id: string;
  /** Human-readable name if provided by the catalogue */
  name?: string;
  /** Any additional metadata the catalogue might supply */
  description?: string;
  location?: string;
  status?: string;
  resolution?: string;
  codec?: string;
  /** Catch-all for unknown fields */
  [key: string]: unknown;
}

/** Response wrapper — handles both array and object-wrapped catalogue shapes. */
export interface CCTVCatalogueResponse {
  cameras: CCTVCamera[];
  totalCount: number;
  fetchedAt: string;
}

// ---------------------------------------------------------------------------
// Playback State Machine
// ---------------------------------------------------------------------------

export type PlaybackState =
  | "IDLE"          // Player created but no stream requested
  | "LOADING"       // Fetching manifest / initializing
  | "BUFFERING"     // Stream attached but buffering data
  | "LIVE"          // Actively playing live content
  | "PAUSED"        // User paused
  | "ERROR"         // Recoverable or fatal error
  | "UNSUPPORTED"   // Codec not supported in this browser
  | "ACCESS_DENIED" // Authentication failure (401/403)
  | "OFFLINE";      // Camera/stream unavailable

export interface PlaybackError {
  state: "ERROR" | "UNSUPPORTED" | "ACCESS_DENIED" | "OFFLINE";
  message: string;
  recoverable: boolean;
  retryCount: number;
}

// ---------------------------------------------------------------------------
// HLS Player Configuration
// ---------------------------------------------------------------------------

export interface HLSStreamConfig {
  /** Maximum concurrent HLS connections allowed across all players */
  maxConcurrentStreams: number;
  /** Initial retry delay in ms */
  initialRetryDelay: number;
  /** Maximum retry delay in ms (cap) */
  maxRetryDelay: number;
  /** Jitter factor (0-1) applied to retry delays */
  jitterFactor: number;
  /** Max retry attempts before giving up (-1 = unlimited) */
  maxRetries: number;
  /** Seconds of stable playback before resetting backoff */
  stablePlaybackThreshold: number;
  /** Whether to attempt autoplay (muted) */
  autoplay: boolean;
}

export const DEFAULT_HLS_CONFIG: HLSStreamConfig = {
  maxConcurrentStreams: 4,
  initialRetryDelay: 2000,
  maxRetryDelay: 30000,
  jitterFactor: 0.25,
  maxRetries: 20,
  stablePlaybackThreshold: 10,
  autoplay: true,
};

// ---------------------------------------------------------------------------
// Catalogue Parsing Utility
// ---------------------------------------------------------------------------

/**
 * Defensively parse the catalogue JSON into a normalised array.
 * Handles: plain array, `{ cameras: [...] }`, `{ data: [...] }`, etc.
 */
export function parseCatalogue(raw: unknown): CCTVCamera[] {
  if (Array.isArray(raw)) {
    return raw.map(normaliseCameraEntry);
  }
  if (raw && typeof raw === "object") {
    const obj = raw as Record<string, unknown>;
    // Try common wrapper keys
    for (const key of ["cameras", "data", "items", "streams", "list"]) {
      if (Array.isArray(obj[key])) {
        return (obj[key] as unknown[]).map(normaliseCameraEntry);
      }
    }
    // Single camera object?
    if (typeof obj.id === "string") {
      return [normaliseCameraEntry(obj)];
    }
  }
  return [];
}

function normaliseCameraEntry(entry: unknown): CCTVCamera {
  if (!entry || typeof entry !== "object") {
    return { id: "unknown" };
  }
  const e = entry as Record<string, unknown>;
  const id = String(e.id ?? e.camera_id ?? e.cameraId ?? e.stream_id ?? "unknown");
  const name = e.name ?? e.title ?? e.label ?? e.camera_name;
  return {
    ...e,
    id,
    name: name ? String(name) : undefined,
  };
}
