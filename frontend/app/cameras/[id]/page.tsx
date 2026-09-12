"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Camera,
  MapPin,
  Activity,
  Cpu,
  Wifi,
  WifiOff,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import LiveStreamPlayer from "@/components/video/LiveStreamPlayer";
import { api, cctvApi, type CCTVCameraEntry } from "@/lib/api";
import type { Camera as CameraType } from "@/lib/types";

export default function CameraDetailPage() {
  const router = useRouter();
  const params = useParams();
  const cameraId = params.id as string;

  const [camera, setCamera] = useState<CameraType | null>(null);
  const [cctvCamera, setCctvCamera] = useState<CCTVCameraEntry | null>(null);
  const [allCameras, setAllCameras] = useState<CCTVCameraEntry[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ---- Load Camera Data ----
  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);

      // Try CDN catalogue first
      try {
        const catalogue = await cctvApi.getCatalogue();
        const allCams = catalogue.cameras || [];
        setAllCameras(allCams);

        const found = allCams.find(
          (c) => c.id.toLowerCase() === cameraId.toLowerCase()
        );
        if (found) {
          setCctvCamera(found);
          setCurrentIndex(allCams.indexOf(found));
          setLoading(false);
          return;
        }
      } catch {
        // CDN failed — try backend
      }

      // Try local backend
      try {
        const cam = await api.getCamera(cameraId);
        setCamera(cam);
      } catch {
        setError("Camera not found");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [cameraId]);

  // ---- Prev / Next Navigation ----
  const canPrev = currentIndex > 0;
  const canNext = currentIndex >= 0 && currentIndex < allCameras.length - 1;

  const navigateTo = useCallback(
    (index: number) => {
      const cam = allCameras[index];
      if (cam) router.push(`/cameras/${cam.id}`);
    },
    [allCameras, router]
  );

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" && canNext) {
        e.preventDefault();
        navigateTo(currentIndex + 1);
      } else if (e.key === "ArrowLeft" && canPrev) {
        e.preventDefault();
        navigateTo(currentIndex - 1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [canPrev, canNext, currentIndex, navigateTo]);

  const displayName = cctvCamera?.name || camera?.name || cameraId;
  const displayId = cctvCamera?.id || camera?.camera_code || cameraId;
  const displayStatus = cctvCamera?.status || camera?.status || "unknown";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-amber-500" />
        <h2 className="text-lg font-medium">{error}</h2>
        <p className="text-sm text-muted mt-1">Camera ID: {cameraId}</p>
        <button
          onClick={() => router.push("/cameras")}
          className="mt-4 px-4 py-2 bg-accent text-white rounded-lg text-sm hover:bg-accent/80 transition"
        >
          Back to Cameras
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/cameras")}
            className="p-2 border border-border rounded-lg hover:bg-surface-hover transition"
            aria-label="Back to cameras"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-lg font-bold text-foreground">{displayName}</h1>
            <p className="text-sm text-muted font-mono">{displayId}</p>
          </div>
        </div>

        {/* Prev/Next */}
        {allCameras.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => canPrev && navigateTo(currentIndex - 1)}
              disabled={!canPrev}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
              aria-label="Previous camera"
            >
              <ChevronLeft className="w-4 h-4" /> Prev
            </button>
            <span className="text-xs text-muted">
              {currentIndex + 1} / {allCameras.length}
            </span>
            <button
              onClick={() => canNext && navigateTo(currentIndex + 1)}
              disabled={!canNext}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
              aria-label="Next camera"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Player (2/3 width) */}
        <div className="lg:col-span-2">
          <LiveStreamPlayer
            key={displayId}
            camera={camera || undefined}
            cctvCamera={cctvCamera || undefined}
            showOverlays={!!camera}
          />
        </div>

        {/* Info Panel (1/3 width) */}
        <div className="space-y-4">
          {/* Status Card */}
          <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
              <Camera className="w-4 h-4 text-accent" /> Camera Info
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-xs text-muted">ID</span>
                <p className="font-mono text-xs">{displayId}</p>
              </div>
              <div>
                <span className="text-xs text-muted">Status</span>
                <p className="flex items-center gap-1">
                  {displayStatus.toLowerCase() === "online" ||
                  displayStatus.toLowerCase() === "live" ? (
                    <Wifi className="w-3 h-3 text-emerald-500" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-red-500" />
                  )}
                  <span className="text-xs">{displayStatus.toUpperCase()}</span>
                </p>
              </div>
              {(cctvCamera?.location || camera?.zone) && (
                <div className="col-span-2">
                  <span className="text-xs text-muted">Location</span>
                  <p className="flex items-center gap-1 text-xs">
                    <MapPin className="w-3 h-3 text-muted" />
                    {cctvCamera?.location || camera?.zone}
                  </p>
                </div>
              )}
              <div>
                <span className="text-xs text-muted">Stream Type</span>
                <p className="text-xs">HLS</p>
              </div>
              <div>
                <span className="text-xs text-muted">Protocol</span>
                <p className="text-xs">{camera?.protocol || "RTSP"}</p>
              </div>
            </div>
          </div>

          {/* Hardware Specs (only for backend cameras) */}
          {camera && (
            <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
                <Cpu className="w-4 h-4 text-accent" /> Hardware
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {camera.manufacturer && (
                  <div>
                    <span className="text-muted">Manufacturer</span>
                    <p>{camera.manufacturer}</p>
                  </div>
                )}
                {camera.model && (
                  <div>
                    <span className="text-muted">Model</span>
                    <p>{camera.model}</p>
                  </div>
                )}
                {camera.resolution && (
                  <div>
                    <span className="text-muted">Resolution</span>
                    <p>{camera.resolution}</p>
                  </div>
                )}
                {camera.fps && (
                  <div>
                    <span className="text-muted">FPS</span>
                    <p>{camera.fps}</p>
                  </div>
                )}
                {camera.latitude && camera.longitude && (
                  <div className="col-span-2">
                    <span className="text-muted">Coordinates</span>
                    <p>{camera.latitude.toFixed(4)}, {camera.longitude.toFixed(4)}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Detections */}
          <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent" /> AI Intelligence
            </h3>
            <p className="text-xs text-muted">
              AI detection events will appear here when the pipeline is processing this camera's stream.
            </p>
          </div>
        </div>
      </div>

      {/* Keyboard Hint */}
      {allCameras.length > 1 && (
        <p className="text-center text-xs text-muted">
          Use <kbd className="px-1 py-0.5 bg-surface border border-border rounded text-xs">←</kbd>{" "}
          <kbd className="px-1 py-0.5 bg-surface border border-border rounded text-xs">→</kbd> arrow keys to navigate between cameras
        </p>
      )}
    </div>
  );
}
