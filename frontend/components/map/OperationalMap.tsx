"use client";

import React, { useState, useEffect } from "react";
import { Camera, Alert } from "@/lib/types";
import { MapPin, Camera as CameraIcon, AlertTriangle, Eye, Play } from "lucide-react";
import Link from "next/link";

interface Props {
  cameras: Camera[];
  alerts?: Alert[];
  selectedCameraId?: string;
  onSelectCamera?: (camera: Camera) => void;
  vehicleRoute?: { plate: string; points: Array<{ lat: number; lng: number; label: string }> };
}

export const OperationalMap: React.FC<Props> = ({
  cameras,
  alerts = [],
  selectedCameraId,
  onSelectCamera,
  vehicleRoute,
}) => {
  const [activeTab, setActiveTab] = useState<"ALL" | "ALERTS" | "CAMERAS">("ALL");
  const [selectedCam, setSelectedCam] = useState<Camera | null>(
    cameras.find((c) => c.id === selectedCameraId) || cameras[0] || null
  );

  // Synchronize internal map state whenever selectedCameraId prop updates from list selection
  useEffect(() => {
    if (selectedCameraId) {
      const match = cameras.find((c) => c.id === selectedCameraId);
      if (match) setSelectedCam(match);
    }
  }, [selectedCameraId, cameras]);

  const handleSelect = (cam: Camera) => {
    setSelectedCam(cam);
    onSelectCamera?.(cam);
  };

  return (
    <div className="relative w-full h-full min-h-[420px] overflow-hidden rounded-2xl border border-slate-300 bg-[#e2f1f8] flex flex-col justify-between shadow-sm">
      {/* Map Header Toolbar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-2 rounded-xl bg-white/95 backdrop-blur border border-slate-300 p-1.5 shadow-md">
          <span className="px-2 text-xs font-black text-[#002147] flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-[#0077b6]" />
            GIS Operations Map
          </span>
          <div className="h-4 w-px bg-slate-300" />
          <button
            onClick={() => setActiveTab("ALL")}
            className={`rounded px-2.5 py-1 text-xs font-extrabold transition-all ${
              activeTab === "ALL" ? "bg-[#0077b6] text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            All Pins ({cameras.length})
          </button>
          <button
            onClick={() => setActiveTab("ALERTS")}
            className={`rounded px-2.5 py-1 text-xs font-extrabold transition-all ${
              activeTab === "ALERTS" ? "bg-[#e11d48] text-white shadow-sm" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            Alerts ({alerts.length})
          </button>
        </div>

        <div className="pointer-events-auto flex items-center gap-2">
          <span className="rounded-lg bg-[#002147] px-3 py-1 text-[11px] font-mono text-[#64dfdf] font-bold shadow-md">
            GUJARAT STATE GIS: 23.0225° N, 72.5714° E
          </span>
        </div>
      </div>

      {/* Interactive GIS Surface */}
      <div className="relative flex-1 w-full bg-[#edf7fc] overflow-hidden p-6 pt-16 flex items-center justify-center">
        {/* Light Map Grid Pattern */}
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(#0077b6 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />

        {/* Vehicle Route SVG Line */}
        {vehicleRoute && (
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            <polyline
              points="150,280 280,180 440,240 560,160"
              fill="none"
              stroke="#e11d48"
              strokeWidth="4"
              strokeDasharray="8 6"
              className="animate-pulse"
            />
          </svg>
        )}

        {/* Map Pins / Camera Nodes */}
        <div className="relative w-full max-w-4xl h-full min-h-[320px] flex items-center justify-center">
          {cameras.map((cam, idx) => {
            const positions = [
              { top: "25%", left: "30%" },
              { top: "45%", left: "60%" },
              { top: "65%", left: "40%" },
              { top: "35%", left: "75%" },
              { top: "70%", left: "70%" },
              { top: "50%", left: "20%" },
              { top: "20%", left: "55%" },
              { top: "80%", left: "30%" },
              { top: "30%", left: "15%" },
              { top: "60%", left: "85%" },
            ];
            const pos = positions[idx % positions.length];
            const isSelected = selectedCam?.id === cam.id;
            const hasAlert = alerts.some((a) => a.camera_id === cam.id);

            return (
              <div
                key={cam.id}
                style={{ top: pos.top, left: pos.left }}
                onClick={() => handleSelect(cam)}
                className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-300 ${
                  isSelected ? "scale-125 z-40" : "hover:scale-110"
                }`}
              >
                {/* Active Highlight Ring when selected */}
                {isSelected && (
                  <div className="absolute -inset-2 rounded-full bg-blue-500/30 animate-ping pointer-events-none" />
                )}

                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 shadow-lg transition-all ${
                    isSelected ? "ring-4 ring-blue-500/80 ring-offset-2 ring-offset-slate-900" : ""
                  } ${
                    hasAlert
                      ? "border-white bg-[#e11d48] text-white animate-bounce"
                      : cam.status === "ONLINE"
                      ? "border-white bg-[#10b981] text-white"
                      : "border-white bg-[#f59e0b] text-white"
                  }`}
                >
                  {hasAlert ? <AlertTriangle className="h-5 w-5" /> : <CameraIcon className="h-5 w-5" />}
                </div>

                <span
                  className={`mt-1 block rounded px-1.5 py-0.5 text-[10px] font-extrabold text-white shadow whitespace-nowrap transition-all ${
                    isSelected ? "bg-blue-600 scale-110" : "bg-[#002147]"
                  }`}
                >
                  {cam.camera_code || cam.name}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Camera Inspector Card */}
      {selectedCam && (
        <div className="z-20 border-t border-slate-300 bg-white p-3 flex flex-wrap items-center justify-between gap-3 shadow-md">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#e2f1f8] border border-[#bde0fe] text-[#0077b6] font-bold">
              <CameraIcon className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-extrabold text-[#002147] text-sm">{selectedCam.name}</p>
                <span className="text-xs font-mono font-bold text-[#0077b6]">[{selectedCam.camera_code}]</span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5 font-medium">
                Zone: <span className="text-slate-900 font-extrabold">{selectedCam.zone}</span> | Lat: {selectedCam.latitude?.toFixed(4)}, Lng: {selectedCam.longitude?.toFixed(4)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleSelect(selectedCam)}
              className="flex items-center gap-1.5 rounded-lg bg-[#10b981] hover:bg-[#059669] px-3.5 py-1.5 text-xs font-extrabold text-white transition-colors shadow"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Stream Live Feed</span>
            </button>
            <Link
              href={`/cameras/${selectedCam.id}`}
              className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-3.5 py-1.5 text-xs font-extrabold text-white transition-colors shadow"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>Full Screen View</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
