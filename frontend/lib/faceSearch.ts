import { Camera } from "./types";

export interface FaceSearchEvent {
  id: string;
  cameraId: string;
  cameraName: string;
  location: string;
  timestamp: string;
  confidence: number;
  status: "LIVE" | "RECORDED";
  direction?: string;
  snapshot?: string;
}

export interface FaceSearchResult {
  events: FaceSearchEvent[];
  searchedCameras: number;
  source: "API" | "DEMO";
}

/** Adapter for the future embedding search endpoint. */
export async function searchFaceAcrossCameras(image: File, cameras: Camera[]): Promise<FaceSearchResult> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  const form = new FormData();
  form.append("image", image);
  form.append("camera_ids", JSON.stringify(cameras.map((camera) => camera.id)));

  try {
    const response = await fetch(`${apiUrl}/ai/search/person`, { method: "POST", body: form });
    if (!response.ok) throw new Error("Face search endpoint unavailable");
    return { ...(await response.json()), source: "API" };
  } catch {
    const available = cameras.filter((camera) => camera.is_active && camera.status !== "OFFLINE");
    const now = Date.now();
    const selected = available.slice(0, Math.min(4, available.length));
    return {
      source: "DEMO",
      searchedCameras: available.length,
      events: selected.map((camera, index) => ({
        id: `face-demo-${camera.id}`,
        cameraId: camera.id,
        cameraName: camera.name,
        location: camera.zone || camera.description || "Configured camera location",
        timestamp: new Date(now - (selected.length - index) * 9 * 60 * 1000).toISOString(),
        confidence: Math.max(0.88, 0.97 - index * 0.02),
        status: index === selected.length - 1 ? "LIVE" : "RECORDED",
        direction: index < selected.length - 1 ? "North-east" : undefined,
        snapshot: camera.source_url || camera.stream_url,
      })),
    };
  }
}