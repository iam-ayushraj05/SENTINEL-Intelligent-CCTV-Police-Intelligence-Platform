"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Camera, Detection } from "@/lib/types";
import { api, MOCK_CAMERAS } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LiveStreamPlayer } from "@/components/video/LiveStreamPlayer";
import { ArrowLeft, Video, Settings, Activity, ShieldCheck, MapPin, Cpu, Clock } from "lucide-react";

export default function CameraDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [camera, setCamera] = useState<Camera | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getCamera(id).then((cam) => {
      setCamera(cam || MOCK_CAMERAS[0]);
    });
  }, [id]);

  if (!camera) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-xs text-slate-500 font-medium">
        Loading CCTV Camera Stream...
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-800">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/cameras"
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 shadow-xs"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-[#002147]">{camera.name}</h1>
              <StatusBadge status={camera.status} />
            </div>
            <p className="text-xs text-slate-600 font-mono font-medium">[{camera.camera_code}] • Zone: {camera.zone}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-lg bg-[#e2f1f8] px-3 py-1 text-xs font-mono text-[#0077b6] font-bold border border-[#bde0fe]">
            Protocol: {camera.protocol}
          </span>
        </div>
      </div>

      {/* Main Grid: Stream Player & Metadata */}
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Large Stream Player */}
        <div className="space-y-4">
          <LiveStreamPlayer camera={camera} showOverlayDefault={true} />

          {/* Camera Recent AI Observations */}
          <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm space-y-3">
            <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
              <Cpu className="h-4 w-4 text-[#0077b6]" />
              <span>Recent AI Detection Stream</span>
            </h2>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-[#f8fafc] p-3.5 border border-slate-200">
                <span className="text-[10px] font-extrabold text-slate-500 uppercase">DETECTION TARGET</span>
                <p className="font-extrabold text-[#002147] text-sm mt-1">Car [TRK-102]</p>
                <p className="text-[11px] text-emerald-700 font-mono font-bold mt-0.5">Confidence: 96%</p>
              </div>
              <div className="rounded-xl bg-[#f8fafc] p-3.5 border border-slate-200">
                <span className="text-[10px] font-extrabold text-slate-500 uppercase">ANPR PLATE OCR</span>
                <p className="font-mono font-black text-[#0077b6] text-sm mt-1">GJ05CD5678</p>
                <p className="text-[11px] text-amber-800 font-extrabold mt-0.5">WATCHLIST MATCH</p>
              </div>
              <div className="rounded-xl bg-[#f8fafc] p-3.5 border border-slate-200">
                <span className="text-[10px] font-extrabold text-slate-500 uppercase">PEDESTRIAN COUNT</span>
                <p className="font-extrabold text-[#002147] text-sm mt-1">4 Active Tracks</p>
                <p className="text-[11px] text-slate-600 mt-0.5 font-medium">Normal trajectory</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Metadata Inspector */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-4 shadow-sm">
            <h2 className="font-extrabold text-[#002147] text-sm border-b border-slate-200 pb-2.5">Camera Specifications</h2>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-500 uppercase text-[10px] font-extrabold block">Manufacturer & Model</span>
                <span className="font-bold text-[#002147]">{camera.manufacturer} {camera.model}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] font-extrabold block">VMS System Reference</span>
                <span className="font-mono text-slate-700 font-bold">{camera.vms_reference || "VMS-GJ-LOCAL"}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] font-extrabold block">RTSP Ingestion URL</span>
                <span className="font-mono text-slate-600 text-[11px] break-all font-medium">{camera.stream_url}</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] font-extrabold block">GIS Coordinates</span>
                <span className="font-mono text-[#002147] font-bold">{camera.latitude}° N, {camera.longitude}° E</span>
              </div>
              <div>
                <span className="text-slate-500 uppercase text-[10px] font-extrabold block">Last Heartbeat</span>
                <span className="text-emerald-700 font-extrabold flex items-center gap-1">
                  <Clock className="h-3 w-3" /> Active (2 seconds ago)
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
            <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-700" />
              <span>Stream Telemetry</span>
            </h2>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-600 font-medium">FPS Rate</span>
                <span className="font-mono font-extrabold text-[#002147]">28.5 FPS</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-600 font-medium">Stream Latency</span>
                <span className="font-mono font-extrabold text-[#002147]">38 ms</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-600 font-medium">Resolution</span>
                <span className="font-mono font-extrabold text-[#002147]">1920x1080 (1080p)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
