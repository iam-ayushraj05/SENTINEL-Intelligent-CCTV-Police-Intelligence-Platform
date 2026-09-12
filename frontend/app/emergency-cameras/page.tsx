"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { fetchAPI } from "@/lib/api";
import type { Camera } from "@/lib/types";

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
  loading: () => <div className="w-full h-full bg-gray-800 flex items-center justify-center">Loading map...</div>,
  ssr: false,
});

const severityColors: Record<string, string> = {
  CRITICAL: "border-red-600 bg-red-900 bg-opacity-20",
  HIGH: "border-orange-600 bg-orange-900 bg-opacity-20",
  MEDIUM: "border-yellow-600 bg-yellow-900 bg-opacity-20",
  LOW: "border-green-600 bg-green-900 bg-opacity-20",
};

const statusColors: Record<string, string> = {
  ONLINE: "bg-green-600",
  OFFLINE: "bg-red-600",
  DEGRADED: "bg-yellow-600",
};

export default function CameraViewPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [filterLocation, setFilterLocation] = useState<string | null>(null);
  const [showFullscreen, setShowFullscreen] = useState(false);

  useEffect(() => {
    loadCameras();
    const interval = setInterval(() => {
      loadCameras();
      if (selectedCamera) loadDetections(selectedCamera.id);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadCameras = async () => {
    try {
      const data = await fetchAPI<Camera[]>("/cameras");
      setCameras(data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load cameras:", error);
    }
  };

  const loadDetections = async (cameraId: string) => {
    try {
      const data = await fetchAPI<Detection[]>(`/detections?camera_id=${cameraId}&limit=10`);
      setDetections(data);
    } catch (error) {
      console.error("Failed to load detections:", error);
    }
  };

  const loadAlerts = async (cameraId: string) => {
    try {
      const data = await fetchAPI<Alert[]>(`/alerts?camera_id=${cameraId}&limit=5`);
      setAlerts(data);
    } catch (error) {
      console.error("Failed to load alerts:", error);
    }
  };

  const handleCameraSelect = (camera: Camera) => {
    setSelectedCamera(camera);
    loadDetections(camera.id);
    loadAlerts(camera.id);
  };

  const filteredCameras = cameras.filter((camera) => {
    if (filterStatus && camera.status !== filterStatus) return false;
    if (filterLocation && camera.zone !== filterLocation) return false;
    return true;
  });

  const locations = [...new Set(cameras.map((c) => c.zone || "General"))];
  const onlineCameras = cameras.filter((c) => c.status === "ONLINE").length;
  const offlineCameras = cameras.filter((c) => c.status === "OFFLINE").length;

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">📹 Multi-Camera Intelligence View</h1>
          <p className="text-gray-400">Real-Time Camera Monitoring & AI Analysis</p>
          <div className="mt-4 flex gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-600 rounded-full"></div>
              <span className="text-sm">Online: {onlineCameras}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-600 rounded-full"></div>
              <span className="text-sm">Offline: {offlineCameras}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-600 rounded-full"></div>
              <span className="text-sm">Total: {cameras.length}</span>
            </div>
          </div>
        </div>

        {/* Map and Cameras Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Map */}
          <div className="lg:col-span-2">
            <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden h-96">
              <MapComponent cameras={filteredCameras} selectedCamera={selectedCamera} onSelectCamera={handleCameraSelect} />
            </div>

            {/* Filters */}
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 mt-4">
              <h3 className="font-bold mb-3">Filters</h3>
              <div className="space-y-2">
                <div>
                  <label className="text-sm text-gray-400">Status</label>
                  <select
                    value={filterStatus || ""}
                    onChange={(e) => setFilterStatus(e.target.value || null)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
                  >
                    <option value="">All Status</option>
                    <option value="ONLINE">Online</option>
                    <option value="OFFLINE">Offline</option>
                    <option value="DEGRADED">Degraded</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-gray-400">Location</label>
                  <select
                    value={filterLocation || ""}
                    onChange={(e) => setFilterLocation(e.target.value || null)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white"
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
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
              <h3 className="text-lg font-bold mb-4">Cameras ({filteredCameras.length})</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredCameras.map((camera) => (
                  <div
                    key={camera.id}
                    onClick={() => handleCameraSelect(camera)}
                    className={`p-3 rounded border-2 cursor-pointer transition ${
                      selectedCamera?.id === camera.id
                        ? "border-blue-500 bg-blue-900 bg-opacity-20"
                        : "border-gray-700 hover:border-gray-600"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-semibold">{camera.name}</p>
                        <p className="text-xs text-gray-400">{camera.camera_code}</p>
                        <p className="text-xs text-gray-300 mt-1">{camera.zone || "General"}</p>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${statusColors[camera.status]}`}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Selected Camera Details */}
        {selectedCamera && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Camera Details */}
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <h3 className="text-xl font-bold mb-4">📋 Camera Details</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-gray-400 text-sm">Camera Name</p>
                  <p className="font-semibold">{selectedCamera.name}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Code</p>
                  <p className="font-semibold">{selectedCamera.camera_code}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Location</p>
                  <p className="font-semibold">{selectedCamera.zone || "General"}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Coordinates</p>
                  <p className="font-semibold text-sm">
                    {selectedCamera.latitude?.toFixed(4)}, {selectedCamera.longitude?.toFixed(4)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Status</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${statusColors[selectedCamera.status]}`}></div>
                    <span className="font-semibold">{selectedCamera.status}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Feed Placeholder */}
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <h3 className="text-xl font-bold mb-4">📹 Live Feed</h3>
              <div className="bg-gray-800 aspect-video rounded flex items-center justify-center">
                <div className="text-center">
                  <p className="text-gray-400">Stream would load here</p>
                  <p className="text-xs text-gray-500 mt-2">{selectedCamera.stream_url}</p>
                </div>
              </div>
              <button
                onClick={() => setShowFullscreen(!showFullscreen)}
                className="w-full mt-3 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-semibold transition"
              >
                {showFullscreen ? "Exit Fullscreen" : "Fullscreen"}
              </button>
            </div>

            {/* AI Analysis */}
            <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <h3 className="text-xl font-bold mb-4">🤖 AI Analysis</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-gray-400 text-sm mb-2">Recent Detections</p>
                  {detections.length > 0 ? (
                    <div className="space-y-2">
                      {detections.slice(0, 5).map((detection) => (
                        <div key={detection.id} className="bg-gray-800 p-2 rounded text-sm">
                          <p className="font-semibold">{detection.object_type}</p>
                          <p className="text-xs text-gray-400">
                            Confidence: {(detection.confidence * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(detection.timestamp).toLocaleString()}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No detections</p>
                  )}
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-2">Active Alerts</p>
                  {alerts.length > 0 ? (
                    <div className="space-y-2">
                      {alerts.slice(0, 3).map((alert) => (
                        <div key={alert.id} className={`p-2 rounded text-sm border ${severityColors[alert.severity]}`}>
                          <p className="font-semibold">{alert.alert_type}</p>
                          <p className="text-xs">{alert.severity}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">No active alerts</p>
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
