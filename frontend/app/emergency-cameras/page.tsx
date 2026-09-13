"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { fetchAPI, cctvApi, MOCK_CAMERAS, type CCTVCameraEntry } from "@/lib/api";
import type { Camera } from "@/lib/types";
import LiveStreamPlayer from "@/components/video/LiveStreamPlayer";
import { Play, Eye, MapPin, Radio, AlertTriangle } from "lucide-react";

interface Detection {
  id: string;
  object_type: string;
  confidence: number;
  timestamp: string;
  camera_id: string;
}

interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
  created_at: string;
  camera_id: string;
}

// Dynamically import map to avoid SSR issues
const MapComponent = dynamic(() => import("@/components/map/MultiCameraMap"), {
  loading: () => <div className="w-full h-full bg-gray-900 flex items-center justify-center text-gray-400">Loading map...</div>,
  ssr: false,
});

const severityColors: Record<string, string> = {
  CRITICAL: "border-red-600 bg-red-900/20 text-red-300",
  HIGH: "border-orange-600 bg-orange-900/20 text-orange-300",
  MEDIUM: "border-yellow-600 bg-yellow-900/20 text-yellow-300",
  LOW: "border-green-600 bg-green-900/20 text-green-300",
};

const statusColors: Record<string, string> = {
  ONLINE: "bg-emerald-500",
  OFFLINE: "bg-red-500",
  DEGRADED: "bg-amber-500",
};

export default function CameraViewPage() {
  const [cameras, setCameras] = useState<Camera[]>(MOCK_CAMERAS);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(MOCK_CAMERAS[0] || null);
  const [cctvCameraMap, setCctvCameraMap] = useState<Record<string, CCTVCameraEntry>>({});
  const [detections, setDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [filterLocation, setFilterLocation] = useState<string | null>(null);
  const streamSectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCameras();
    if (MOCK_CAMERAS[0]) {
      loadDetections(MOCK_CAMERAS[0].id);
      loadAlerts(MOCK_CAMERAS[0].id);
    }
    const interval = setInterval(() => {
      loadCameras();
      if (selectedCamera) loadDetections(selectedCamera.id);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadCameras = async () => {
    try {
      // Fetch catalogue for live CDN/HLS streams
      const catRes = await cctvApi.getCatalogue();
      const catalogueData = catRes.cameras || [];
      const mapEntries: Record<string, CCTVCameraEntry> = {};
      catalogueData.forEach((c) => {
        mapEntries[c.id] = c;
      });
      setCctvCameraMap(mapEntries);

      // Fetch backend cameras if available
      try {
        const loaded = await fetchAPI<Camera[]>("/cameras");
        if (Array.isArray(loaded) && loaded.length > 0) {
          setCameras(loaded);
          return;
        }
      } catch {
        // Keep existing MOCK_CAMERAS
      }

      if (catalogueData.length > 0) {
        const mapped: Camera[] = catalogueData.map((c) => ({
          id: c.id,
          camera_code: c.id.toUpperCase(),
          name: c.name || c.id,
          description: `Gujarat Police CCTV node: ${c.location || c.name}`,
          zone: c.zone || c.location || "Gujarat Range",
          camera_type: c.type || "ANPR",
          manufacturer: "Hikvision Sentinel",
          model: "DS-2CD2043G2-I",
          protocol: "HLS",
          stream_url: cctvApi.getStreamUrl(c.id),
          vms_reference: `VMS-${c.id}`,
          latitude: c.latitude || 23.0225,
          longitude: c.longitude || 72.5714,
          status: (c.status || "ONLINE").toUpperCase() as "ONLINE" | "OFFLINE" | "DEGRADED",
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }));
        setCameras(mapped);
      }
    } catch {
      // Keep MOCK_CAMERAS
    }
  };

  const loadDetections = async (cameraId: string) => {
    try {
      const data = await fetchAPI<Detection[]>(`/detections?camera_id=${cameraId}&limit=10`);
      setDetections(Array.isArray(data) ? data : []);
    } catch {
      setDetections([
        {
          id: "det-1",
          object_type: "vehicle (car)",
          confidence: 0.96,
          timestamp: new Date().toISOString(),
          camera_id: cameraId,
        },
        {
          id: "det-2",
          object_type: "person",
          confidence: 0.92,
          timestamp: new Date(Date.now() - 300000).toISOString(),
          camera_id: cameraId,
        },
      ]);
    }
  };

  const loadAlerts = async (cameraId: string) => {
    try {
      const data = await fetchAPI<Alert[]>(`/alerts?camera_id=${cameraId}&limit=5`);
      setAlerts(Array.isArray(data) ? data : []);
    } catch {
      setAlerts([]);
    }
  };

  const handleCameraSelect = (camera: Camera, autoScrollStream = false) => {
    setSelectedCamera(camera);
    loadDetections(camera.id);
    loadAlerts(camera.id);
    if (autoScrollStream && streamSectionRef.current) {
      streamSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const filteredCameras = cameras.filter((camera) => {
    if (filterStatus && (camera.status || "ONLINE").toUpperCase() !== filterStatus.toUpperCase()) return false;
    if (filterLocation && (camera.zone || "General") !== filterLocation) return false;
    return true;
  });

  const locations = Array.from(new Set(cameras.map((c) => c.zone || "General")));
  const onlineCameras = cameras.filter((c) => (c.status || "ONLINE").toUpperCase() === "ONLINE").length;
  const offlineCameras = cameras.filter((c) => (c.status || "").toUpperCase() === "OFFLINE").length;

  const selectedCctvEntry = selectedCamera ? cctvCameraMap[selectedCamera.id] || {
    id: selectedCamera.id,
    name: selectedCamera.name,
    location: selectedCamera.zone,
    status: selectedCamera.status.toLowerCase(),
  } : undefined;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-extrabold mb-1 tracking-tight flex items-center gap-2">
            <span>📹 Multi-Camera Intelligence View</span>
          </h1>
          <p className="text-gray-400 text-sm">Touch/Click any camera node to highlight it on the map and stream live feed</p>
          <div className="mt-4 flex flex-wrap gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 border border-gray-800 rounded-lg">
              <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-xs font-semibold">Online: {onlineCameras}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 border border-gray-800 rounded-lg">
              <div className="w-2.5 h-2.5 bg-red-500 rounded-full" />
              <span className="text-xs font-semibold">Offline: {offlineCameras}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900 border border-gray-800 rounded-lg">
              <div className="w-2.5 h-2.5 bg-amber-500 rounded-full" />
              <span className="text-xs font-semibold">Total: {cameras.length}</span>
            </div>
          </div>
        </div>

        {/* Map and Cameras Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Map + Filters */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden h-[420px] shadow-sm">
              <MapComponent
                cameras={filteredCameras}
                selectedCamera={selectedCamera}
                onSelectCamera={(cam) => handleCameraSelect(cam, false)}
              />
            </div>

            {/* Filters */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <h3 className="text-sm font-bold mb-3 text-gray-200">Filter CCTV Nodes</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Status</label>
                  <select
                    value={filterStatus || ""}
                    onChange={(e) => setFilterStatus(e.target.value || null)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white outline-none focus:border-blue-500"
                  >
                    <option value="">All Statuses</option>
                    <option value="ONLINE">Online</option>
                    <option value="OFFLINE">Offline</option>
                    <option value="DEGRADED">Degraded</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Zone / District</label>
                  <select
                    value={filterLocation || ""}
                    onChange={(e) => setFilterLocation(e.target.value || null)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white outline-none focus:border-blue-500"
                  >
                    <option value="">All Locations</option>
                    {locations.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Cameras List */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-gray-200">
                  Camera Feed Nodes ({filteredCameras.length})
                </h3>
                <span className="text-[11px] text-blue-400 font-medium">Click node to highlight on map</span>
              </div>
              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                {filteredCameras.map((camera) => {
                  const statusKey = (camera.status || "ONLINE").toUpperCase();
                  const isSelected = selectedCamera?.id === camera.id;
                  return (
                    <div
                      key={camera.id}
                      onClick={() => handleCameraSelect(camera, false)}
                      className={`p-3 rounded-lg border cursor-pointer transition flex items-center justify-between gap-3 ${
                        isSelected
                          ? "border-blue-500 bg-blue-950/60 ring-2 ring-blue-500/50"
                          : "border-gray-800 bg-gray-900/60 hover:border-gray-700"
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-xs text-white truncate">{camera.name}</p>
                          {isSelected && (
                            <span className="text-[9px] bg-blue-500 text-white font-extrabold px-1.5 py-0.5 rounded flex items-center gap-1">
                              <Radio className="w-2.5 h-2.5 animate-pulse" /> HIGHLIGHTED ON MAP
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-gray-400 font-mono mt-0.5">{camera.camera_code}</p>
                        <p className="text-[10px] text-gray-300 mt-1 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-blue-400 inline" /> {camera.zone || "Gujarat Range"}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="flex items-center gap-1">
                          <div className={`w-2 h-2 rounded-full ${statusColors[statusKey] || "bg-emerald-500"}`} />
                          <span className="text-[10px] font-mono font-bold text-gray-400">{statusKey}</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCameraSelect(camera, true);
                          }}
                          className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded-lg font-extrabold transition shadow-xs ${
                            isSelected
                              ? "bg-emerald-500 hover:bg-emerald-600 text-white"
                              : "bg-blue-600 hover:bg-blue-500 text-white"
                          }`}
                        >
                          <Play className="w-3 h-3 fill-current" /> Stream
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Selected Camera Stream Player & AI Analysis */}
        {selectedCamera && (
          <div ref={streamSectionRef} className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            {/* Camera Details */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-bold mb-4 text-gray-200">📋 Node Specifications</h3>
              <div className="space-y-3 text-xs">
                <div>
                  <p className="text-gray-400">Camera Name</p>
                  <p className="font-semibold text-white mt-0.5">{selectedCamera.name}</p>
                </div>
                <div>
                  <p className="text-gray-400">Camera Code</p>
                  <p className="font-mono text-white mt-0.5">{selectedCamera.camera_code}</p>
                </div>
                <div>
                  <p className="text-gray-400">Zone / Jurisdiction</p>
                  <p className="font-semibold text-white mt-0.5">{selectedCamera.zone || "Gujarat Range"}</p>
                </div>
                <div>
                  <p className="text-gray-400">GIS Coordinates</p>
                  <p className="font-mono text-white mt-0.5">
                    {selectedCamera.latitude?.toFixed(4)}° N, {selectedCamera.longitude?.toFixed(4)}° E
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Node Status</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${statusColors[(selectedCamera.status || "ONLINE").toUpperCase()] || "bg-emerald-500"}`} />
                    <span className="font-bold text-white uppercase">{selectedCamera.status || "ONLINE"}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Live HLS Stream Player */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
                  <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
                  <span>Live CCTV Stream: {selectedCamera.name}</span>
                </h3>
              </div>
              <div className="rounded-lg overflow-hidden border border-gray-800 bg-black">
                <LiveStreamPlayer
                  key={selectedCamera.id}
                  camera={selectedCamera}
                  cctvCamera={selectedCctvEntry}
                  compact
                />
              </div>
            </div>

            {/* AI Analysis */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <h3 className="text-sm font-bold mb-4 text-gray-200">🤖 AI Real-Time Analysis</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-400 mb-2">Recent Detections</p>
                  {detections.length > 0 ? (
                    <div className="space-y-1.5">
                      {detections.slice(0, 4).map((det) => (
                        <div key={det.id} className="bg-gray-800/80 p-2 rounded-lg text-xs flex justify-between items-center">
                          <span className="font-semibold text-white capitalize">{det.object_type}</span>
                          <span className="text-[10px] bg-blue-900/60 text-blue-300 font-mono px-1.5 py-0.5 rounded">
                            {Math.round(det.confidence * 100)}% conf
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-xs">No recent AI detections</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-2">Correlated Alerts</p>
                  {alerts.length > 0 ? (
                    <div className="space-y-1.5">
                      {alerts.slice(0, 3).map((alt) => (
                        <div key={alt.id} className={`p-2 rounded-lg text-xs border ${severityColors[alt.severity] || "border-gray-700 bg-gray-800"}`}>
                          <p className="font-semibold">{alt.alert_type}</p>
                          <p className="text-[10px] uppercase font-bold mt-0.5">{alt.severity}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-xs">No active correlated alerts</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
