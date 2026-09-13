"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Grid2X2,
  Grid3X3,
  LayoutGrid,
  List,
  Square,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Camera,
  Wifi,
  WifiOff,
  AlertTriangle,
  Loader2,
  Monitor,
} from "lucide-react";
import LiveStreamPlayer from "@/components/video/LiveStreamPlayer";
import { cctvApi, type CCTVCameraEntry } from "@/lib/api";

type LayoutMode = "2x2" | "3x3" | "4x4" | "LIST" | "SLIDE";

const LAYOUT_CONFIGS: Record<string, { cols: string; maxVisible: number }> = {
  "2x2": { cols: "grid-cols-1 sm:grid-cols-2", maxVisible: 4 },
  "3x3": { cols: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3", maxVisible: 9 },
  "4x4": { cols: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4", maxVisible: 16 },
};

const MAX_CONCURRENT_STREAMS = 4;

export default function CamerasPage() {
  const router = useRouter();
  const [cameras, setCameras] = useState<CCTVCameraEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catalogueSource, setCatalogueSource] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [layout, setLayout] = useState<LayoutMode>("3x3");
  const [gridPage, setGridPage] = useState(0);
  const [slideIndex, setSlideIndex] = useState(0);

  // ---- Fetch Camera Catalogue ----
  const fetchCatalogue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await cctvApi.getCatalogue();
      setCameras(response.cameras || []);
      setCatalogueSource(response.source || "unknown");
      if (response.status === "AUTH_FAILED") {
        setError("CDN authentication failed — showing fallback cameras");
      } else if (response.status === "CCTV_CONFIG_MISSING") {
        setError("CDN credentials not configured — showing fallback cameras");
      }
    } catch (e) {
      setError("Failed to load camera catalogue");
      setCameras([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCatalogue();
  }, [fetchCatalogue]);

  // ---- Filtering ----
  const filteredCameras = useMemo(() => {
    let result = cameras;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.id.toLowerCase().includes(q) ||
          (c.name || "").toLowerCase().includes(q) ||
          (c.location || "").toLowerCase().includes(q)
      );
    }
    if (statusFilter !== "ALL") {
      result = result.filter(
        (c) => (c.status || "online").toLowerCase() === statusFilter.toLowerCase()
      );
    }
    return result;
  }, [cameras, searchQuery, statusFilter]);

  // ---- Grid Pagination ----
  const layoutConfig = LAYOUT_CONFIGS[layout] || { cols: "", maxVisible: 1 };
  const gridCameras = useMemo(() => {
    if (layout === "LIST" || layout === "SLIDE") return filteredCameras;
    const start = gridPage * layoutConfig.maxVisible;
    return filteredCameras.slice(start, start + layoutConfig.maxVisible);
  }, [filteredCameras, layout, gridPage, layoutConfig.maxVisible]);

  const totalGridPages = Math.ceil(filteredCameras.length / (layoutConfig.maxVisible || 1));

  // ---- Slide Navigation ----
  const currentSlideCamera = filteredCameras[slideIndex] || null;

  const handleSlideNext = useCallback(() => {
    setSlideIndex((i) => Math.min(i + 1, filteredCameras.length - 1));
  }, [filteredCameras.length]);

  const handleSlidePrev = useCallback(() => {
    setSlideIndex((i) => Math.max(i - 1, 0));
  }, []);

  // Keyboard navigation
  useEffect(() => {
    if (layout !== "SLIDE") return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        handleSlideNext();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        handleSlidePrev();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [layout, handleSlideNext, handleSlidePrev]);

  // ---- Active streams tracking (matches selected grid layout capacity) ----
  const activeCameras = useMemo(() => {
    if (layout === "SLIDE") return currentSlideCamera ? [currentSlideCamera] : [];
    if (layout === "LIST") return [];
    return gridCameras.slice(0, layoutConfig.maxVisible);
  }, [layout, gridCameras, currentSlideCamera, layoutConfig.maxVisible]);

  return (
    <div className="p-4 md:p-6 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
            <Monitor className="w-5 h-5 text-accent" />
            CCTV Video Wall
          </h1>
          <p className="text-sm text-muted mt-0.5">
            {loading
              ? "Loading cameras…"
              : `Showing ${filteredCameras.length} of ${cameras.length} cameras`}
            {catalogueSource && !loading && (
              <span className="text-xs text-muted ml-2">({catalogueSource})</span>
            )}
          </p>
        </div>
        <button
          onClick={fetchCatalogue}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-surface border border-border rounded-lg hover:bg-surface-hover transition"
          disabled={loading}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filters & Layout Selector */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            placeholder="Search cameras by ID, name, or location…"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setGridPage(0);
              setSlideIndex(0);
            }}
            className="w-full pl-9 pr-3 py-2 text-sm bg-surface border border-border rounded-lg focus:ring-2 focus:ring-accent/30 focus:border-accent outline-none"
          />
        </div>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setGridPage(0);
            setSlideIndex(0);
          }}
          className="px-3 py-2 text-sm bg-surface border border-border rounded-lg"
        >
          <option value="ALL">All Status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
          <option value="degraded">Degraded</option>
        </select>

        {/* Layout */}
        <div className="flex border border-border rounded-lg overflow-hidden">
          {[
            { mode: "2x2" as const, icon: Grid2X2, label: "2×2" },
            { mode: "3x3" as const, icon: Grid3X3, label: "3×3" },
            { mode: "4x4" as const, icon: LayoutGrid, label: "4×4" },
            { mode: "LIST" as const, icon: List, label: "List" },
            { mode: "SLIDE" as const, icon: Square, label: "Slide" },
          ].map(({ mode, icon: Icon, label }) => (
            <button
              key={mode}
              onClick={() => {
                setLayout(mode);
                setGridPage(0);
                setSlideIndex(0);
              }}
              className={`p-2 text-sm transition ${
                layout === mode
                  ? "bg-accent text-white"
                  : "bg-surface text-muted hover:bg-surface-hover"
              }`}
              title={label}
              aria-label={`${label} layout`}
            >
              <Icon className="w-4 h-4" />
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredCameras.length === 0 && (
        <div className="text-center py-20 text-muted">
          <Camera className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-lg font-medium">No cameras found</p>
          <p className="text-sm mt-1">
            {searchQuery
              ? "Try a different search query"
              : "Camera catalogue is empty"}
          </p>
        </div>
      )}

      {/* ---- GRID VIEW ---- */}
      {!loading && layout !== "LIST" && layout !== "SLIDE" && filteredCameras.length > 0 && (
        <>
          <div className={`grid ${layoutConfig.cols} gap-3`}>
            {gridCameras.map((cam) => {
              const isActive = activeCameras.some((a) => a.id === cam.id);
              return (
                <div
                  key={cam.id}
                  className="bg-surface border border-border rounded-lg overflow-hidden cursor-pointer hover:border-accent/50 transition"
                  onClick={() => router.push(`/cameras/${cam.id}`)}
                >
                  {isActive ? (
                    <LiveStreamPlayer cctvCamera={cam} compact />
                  ) : (
                    <div className="aspect-video bg-gray-900 flex items-center justify-center">
                      <div className="text-center text-gray-500">
                        <Camera className="w-6 h-6 mx-auto mb-1" />
                        <p className="text-xs">{cam.name || cam.id}</p>
                        <p className="text-[10px] text-gray-600">Click to view</p>
                      </div>
                    </div>
                  )}
                  <div className="px-2 py-1.5 flex items-center justify-between">
                    <span className="text-xs font-medium text-foreground truncate">
                      {cam.name || cam.id}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${
                      (cam.status || "online").toLowerCase() === "online"
                        ? "bg-emerald-500"
                        : "bg-red-500"
                    }`} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Grid Pagination */}
          {totalGridPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setGridPage((p) => Math.max(p - 1, 0))}
                disabled={gridPage === 0}
                className="p-1.5 border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
                aria-label="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-muted">
                Page {gridPage + 1} of {totalGridPages}
              </span>
              <button
                onClick={() => setGridPage((p) => Math.min(p + 1, totalGridPages - 1))}
                disabled={gridPage >= totalGridPages - 1}
                className="p-1.5 border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
                aria-label="Next page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}

      {/* ---- LIST VIEW ---- */}
      {!loading && layout === "LIST" && filteredCameras.length > 0 && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-bg-secondary text-muted text-left">
              <tr>
                <th className="px-4 py-2">Camera ID</th>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Location</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Stream</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-light">
              {filteredCameras.map((cam) => (
                <tr
                  key={cam.id}
                  className="hover:bg-surface-hover cursor-pointer transition"
                  onClick={() => router.push(`/cameras/${cam.id}`)}
                >
                  <td className="px-4 py-2 font-mono text-xs">{cam.id}</td>
                  <td className="px-4 py-2">{cam.name || cam.id}</td>
                  <td className="px-4 py-2 text-muted">{cam.location || "—"}</td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${
                      (cam.status || "online").toLowerCase() === "online"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {(cam.status || "online").toLowerCase() === "online" ? (
                        <Wifi className="w-3 h-3" />
                      ) : (
                        <WifiOff className="w-3 h-3" />
                      )}
                      {(cam.status || "online").toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-xs text-accent">HLS</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---- SLIDE VIEW ---- */}
      {!loading && layout === "SLIDE" && filteredCameras.length > 0 && currentSlideCamera && (
        <div className="space-y-3">
          {/* Slide Navigation Header */}
          <div className="flex items-center justify-between bg-surface border border-border rounded-lg px-4 py-2">
            <button
              onClick={handleSlidePrev}
              disabled={slideIndex === 0}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
              aria-label="Previous camera"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>
            <div className="text-center">
              <select
                value={slideIndex}
                onChange={(e) => setSlideIndex(Number(e.target.value))}
                className="text-sm font-medium bg-transparent border-none focus:ring-0 text-center cursor-pointer"
              >
                {filteredCameras.map((cam, i) => (
                  <option key={cam.id} value={i}>
                    {cam.name || cam.id}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted">
                Camera {slideIndex + 1} of {filteredCameras.length}
              </p>
            </div>
            <button
              onClick={handleSlideNext}
              disabled={slideIndex >= filteredCameras.length - 1}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover disabled:opacity-30 transition"
              aria-label="Next camera"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Slide Player */}
          <div className="max-w-4xl mx-auto">
            <LiveStreamPlayer
              key={currentSlideCamera.id}
              cctvCamera={currentSlideCamera}
            />
          </div>

          {/* Camera Info */}
          <div className="max-w-4xl mx-auto bg-surface border border-border rounded-lg px-4 py-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div>
                <span className="text-muted text-xs">Camera ID</span>
                <p className="font-mono">{currentSlideCamera.id}</p>
              </div>
              <div>
                <span className="text-muted text-xs">Name</span>
                <p>{currentSlideCamera.name || currentSlideCamera.id}</p>
              </div>
              <div>
                <span className="text-muted text-xs">Location</span>
                <p>{currentSlideCamera.location || "Gujarat Range"}</p>
              </div>
              <div>
                <span className="text-muted text-xs">Status</span>
                <p className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${
                    (currentSlideCamera.status || "online").toLowerCase() === "online"
                      ? "bg-emerald-500"
                      : "bg-red-500"
                  }`} />
                  {(currentSlideCamera.status || "online").toUpperCase()}
                </p>
              </div>
            </div>
          </div>

          {/* Keyboard Hint */}
          <p className="text-center text-xs text-muted">
            Use <kbd className="px-1 py-0.5 bg-surface border border-border rounded text-xs">←</kbd>{" "}
            <kbd className="px-1 py-0.5 bg-surface border border-border rounded text-xs">→</kbd> arrow keys to navigate
          </p>
        </div>
      )}
    </div>
  );
}
