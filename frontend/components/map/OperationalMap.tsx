"use client";

import React, { useState } from "react";
import { Camera, Alert } from "@/lib/types";
import { MapPin, Camera as CameraIcon, AlertTriangle, Layers, Car, Eye } from "lucide-react";
import Link from "next/link";

interface Props {
  cameras: Camera[];
  alerts?: Alert[];
  selectedCameraId?: string;
  vehicleRoute?: { plate: string; points: Array<{ lat: number; lng: number; label: string }> };
}

export const OperationalMap: React.FC<Props> = ({ cameras, alerts = [], selectedCameraId, vehicleRoute }) => {
  const [activeTab, setActiveTab] = useState<"ALL" | "ALERTS" | "CAMERAS">("ALL");
  const [selectedCam, setSelectedCam] = useState<Camera | null>(
    cameras.find((c) => c.id === selectedCameraId) || cameras[0] || null
  );

  return (
    <div className="relative w-full h-full min-h-[440px] overflow-hidden rounded-2xl border border-[#cbd5e1] bg-[#e2f1f8] flex flex-col justify-between shadow-sm">
      {/* Map Header Toolbar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-2 rounded-xl bg-white border border-[#cbd5e1] p-1.5 shadow-md">
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
            GUJARAT STATE GIS COORDS: 23.0225° N, 72.5714° E
          </span>
        </div>
      </div>

      {/* Simulated Interactive GIS Surface (Light Canvas) */}
      <div className="relative flex-1 w-full bg-[#edf7fc] overflow-hidden p-6 pt-16 flex items-center justify-center">
        {/* Light Map Grid Pattern */}
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(#0077b6 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />

        {/* Vehicle Route SVG Line if provided */}
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
        <div className="relative w-full max-w-4xl h-full min-h-[340px] flex items-center justify-center">
          {cameras.map((cam, idx) => {
            const positions = [
              { top: "25%", left: "30%" },
              { top: "45%", left: "60%" },
              { top: "65%", left: "40%" },
              { top: "35%", left: "75%" },
              { top: "70%", left: "70%" },
              { top: "50%", left: "20%" },
            ];
            const pos = positions[idx % positions.length];
            const isSelected = selectedCam?.id === cam.id;
            const hasAlert = alerts.some((a) => a.camera_id === cam.id);

            return (
              <div
                key={cam.id}
                style={{ top: pos.top, left: pos.left }}
                onClick={() => setSelectedCam(cam)}
                className={`absolute z-20 -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all duration-200 ${
                  isSelected ? "scale-125 z-30" : "hover:scale-110"
                }`}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full border-2 shadow-lg ${
                    hasAlert
                      ? "border-white bg-[#e11d48] text-white animate-bounce"
                      : cam.status === "ONLINE"
                      ? "border-white bg-[#10b981] text-white"
                      : "border-white bg-[#f59e0b] text-white"
                  }`}
                >
                  {hasAlert ? <AlertTriangle className="h-5 w-5" /> : <CameraIcon className="h-5 w-5" />}
                </div>
                <span className="mt-1 block rounded bg-[#002147] px-1.5 py-0.5 text-[10px] font-extrabold text-white shadow whitespace-nowrap">
                  {cam.camera_code}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Camera Inspector Card (Pure White Bottom Bar) */}
      {selectedCam && (
        <div className="z-20 border-t border-[#cbd5e1] bg-white p-4 flex flex-wrap items-center justify-between gap-4 shadow-md">
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
                Zone: <span className="text-slate-900 font-extrabold">{selectedCam.zone}</span> | Lat: {selectedCam.latitude}, Lng: {selectedCam.longitude}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/cameras/${selectedCam.id}`}
              className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white transition-colors shadow"
            >
              <Eye className="h-4 w-4" />
              <span>Open Live Stream</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
