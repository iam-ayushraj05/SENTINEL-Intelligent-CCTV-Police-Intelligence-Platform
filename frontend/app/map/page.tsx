"use client";

import React, { useEffect, useState } from "react";
import { Camera, Alert } from "@/lib/types";
import { api, MOCK_CAMERAS, MOCK_ALERTS } from "@/lib/api";
import { OperationalMap } from "@/components/map/OperationalMap";
import { MapPin, Filter, Layers, Video } from "lucide-react";

export default function MapPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    api.getCameras().then((c) => setCameras(c.length ? c : MOCK_CAMERAS));
    api.getAlerts().then((a) => setAlerts(a.length ? a : MOCK_ALERTS));
  }, []);

  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col text-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-300 pb-3">
        <div>
          <h1 className="text-xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <MapPin className="h-5 w-5 text-[#0077b6]" />
            <span>GUJARAT STATE GIS SURVEILLANCE MAP</span>
          </h1>
          <p className="text-xs text-slate-600 font-medium">
            Tactical GIS Map Displaying Live CCTV Nodes & Active Alert Geolocation
          </p>
        </div>
      </div>

      {/* Map Surface */}
      <div className="flex-1 w-full rounded-2xl overflow-hidden border border-[#cbd5e1] bg-white shadow-sm">
        <OperationalMap cameras={cameras.length ? cameras : MOCK_CAMERAS} alerts={alerts.length ? alerts : MOCK_ALERTS} />
      </div>
    </div>
  );
}
