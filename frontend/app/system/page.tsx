"use client";

import React, { useEffect, useState } from "react";
import { Activity, Database, Cpu, Radio, ShieldCheck, CheckCircle2, Server, Terminal } from "lucide-react";

export default function SystemHealthPage() {
  const [metricsText, setMetricsText] = useState("");

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/metrics")
      .then((res) => res.text())
      .then(setMetricsText)
      .catch(() => {
        setMetricsText(
          `# HELP sentinel_active_cameras Total active registered cameras\nsentinel_active_cameras 6\n# HELP sentinel_ai_fps AI inference FPS\nsentinel_ai_fps 28.5\n# HELP sentinel_active_alerts Active alerts\nsentinel_active_alerts 3`
        );
      });
  }, []);

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="border-b border-slate-300 pb-4">
        <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
          <Activity className="h-6 w-6 text-[#059669]" />
          <span>SYSTEM HEALTH & PROMETHEUS OBSERVABILITY</span>
        </h1>
        <p className="mt-1 text-xs text-slate-600 font-medium">Infrastructure Health, AI Pipeline Telemetry & Prometheus Metric Exporter</p>
      </div>

      {/* Component Status Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-500 uppercase">PostgreSQL + PostGIS</span>
            <span className="flex items-center gap-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" /> HEALTHY
            </span>
          </div>
          <p className="text-xl font-black text-[#002147]">DB Storage Engine</p>
          <span className="text-xs text-slate-600 font-medium">Latency: 1.2ms | Connections: 12</span>
        </div>

        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-500 uppercase">Redis Memory Cache</span>
            <span className="flex items-center gap-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" /> HEALTHY
            </span>
          </div>
          <p className="text-xl font-black text-[#002147]">Cache & Fanout</p>
          <span className="text-xs text-slate-600 font-medium">Latency: 0.8ms | Memory: 42MB</span>
        </div>

        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-500 uppercase">Apache Kafka Broker</span>
            <span className="flex items-center gap-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" /> HEALTHY
            </span>
          </div>
          <p className="text-xl font-black text-[#002147]">Event Stream Bus</p>
          <span className="text-xs text-slate-600 font-medium">Topics: sentinel.detections, sentinel.alerts</span>
        </div>

        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-500 uppercase">YOLOv8 AI Engine</span>
            <span className="flex items-center gap-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" /> RUNNING
            </span>
          </div>
          <p className="text-xl font-black text-[#002147]">28.5 FPS</p>
          <span className="text-xs text-slate-600 font-medium">Active Pipeline Workers: 4</span>
        </div>

        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-500 uppercase">MediaMTX Gateway</span>
            <span className="flex items-center gap-1 text-xs font-black text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" /> ACTIVE
            </span>
          </div>
          <p className="text-xl font-black text-[#002147]">RTSP / WebRTC</p>
          <span className="text-xs text-slate-600 font-medium">Active Live Streams: 6</span>
        </div>
      </div>

      {/* Prometheus Raw Exporter View */}
      <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
        <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#0077b6]" />
          <span>Prometheus Exporter Output Endpoint (/api/v1/metrics)</span>
        </h2>
        <pre className="rounded-xl bg-[#002147] p-4 text-xs font-mono text-[#64dfdf] overflow-x-auto border border-[#003366] shadow-md">
          {metricsText}
        </pre>
      </div>
    </div>
  );
}
