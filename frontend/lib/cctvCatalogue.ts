import type { CCTVCamera } from "./cctvTypes";

export const CCTV_CATALOGUE_URL = "https://cctv.corp8.cloud/cameras.json";
export const CCTV_HLS_ORIGIN = "https://cctv.corp8.cloud";

export class CatalogueError extends Error {
  readonly kind: "AUTHENTICATION" | "NETWORK" | "INVALID";
  readonly status?: number;

  constructor(kind: CatalogueError["kind"], message: string, status?: number) {
    super(message);
    this.name = "CatalogueError";
    this.kind = kind;
    this.status = status;
  }
}

export async function fetchCCTVCatalogue(signal?: AbortSignal): Promise<CCTVCamera[]> {
  let response: Response;
  try {
    response = await fetch(CCTV_CATALOGUE_URL, {
      credentials: "include",
      cache: "no-store",
      signal,
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new CatalogueError("NETWORK", "The catalogue request was blocked by the browser. Confirm CCTV CORS allows this site and that your CCTV sign-in session is active.");
  }

  if (response.status === 401 || response.status === 403 || response.redirected) {
    throw new CatalogueError("AUTHENTICATION", "CCTV access is required for the camera catalogue.", response.status);
  }
  if (!response.ok) {
    throw new CatalogueError("NETWORK", `The camera catalogue returned HTTP ${response.status}.`, response.status);
  }

  const contentType = response.headers.get("content-type") || "";
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new CatalogueError(
      contentType.includes("text/html") ? "AUTHENTICATION" : "INVALID",
      contentType.includes("text/html")
        ? "CCTV authentication is required before the catalogue can be read."
        : "The camera catalogue was not valid JSON.",
    );
  }

  const cameras = parseCatalogue(payload);
  if (!Array.isArray(cameras)) {
    throw new CatalogueError("INVALID", "The camera catalogue has an unsupported shape.");
  }
  return cameras;
}

export function parseCatalogue(payload: unknown): CCTVCamera[] {
  const entries = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object"
      ? Object.values(payload as Record<string, unknown>).find(Array.isArray) || []
      : [];

  return (entries as unknown[])
    .filter((entry): entry is Record<string, unknown> => Boolean(entry && typeof entry === "object"))
    .map((entry) => {
      const id = entry.id ?? entry.camera_id ?? entry.cameraId ?? entry.stream_id;
      return {
        ...entry,
        id: typeof id === "string" || typeof id === "number" ? String(id) : "",
        name: typeof (entry.name ?? entry.title ?? entry.label ?? entry.camera_name) === "string"
          ? String(entry.name ?? entry.title ?? entry.label ?? entry.camera_name)
          : undefined,
      };
    })
    .filter((camera) => camera.id.length > 0);
}

export function hlsUrlForCamera(cameraId: string): string {
  return `${CCTV_HLS_ORIGIN}/${encodeURIComponent(cameraId)}/index.m3u8`;
}

export function cameraLabel(camera: CCTVCamera): string {
  return camera.name?.trim() || camera.id;
}
