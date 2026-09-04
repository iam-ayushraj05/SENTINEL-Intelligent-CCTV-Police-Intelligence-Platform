"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Camera, Alert, DashboardSummary } from "@/lib/types";
import { api, MOCK_CAMERAS, MOCK_ALERTS } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { StatCard } from "@/components/ui/StatCard";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { OperationalMap } from "@/components/map/OperationalMap";
import { Video, Bell, Cpu, Car, Activity, ArrowRight, ShieldAlert, CheckCircle2, Server, Clock } from "lucide-react";

export default function CommandDashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [liveLog, setLiveLog] = useState<{ time: string; text: string; type: string }[]>([
    { time: "18:32", text: "Watchlist match alert ALT-20260904-9981 generated on CAM-GJ01-001", type: "ALERT" },
    { time: "18:29", text: "ANPR plate GJ05CD5678 detected & correlated against VAHAN_POLICE_FIR", type: "ANPR" },
    { time: "18:26", text: "CAM-GJ03-001 stream recovered from degraded state to 28 FPS", type: "CAMERA" },
    { time: "18:20", text: "Case #CASE-2026-GJ-0091 updated with frame snapshot evidence", type: "CASE" },
  ]);

  useEffect(() => {
    // Load initial state
    api.getDashboardSummary().then(setSummary);
    api.getCameras().then(setCameras);
    api.getAlerts().then(setAlerts);

    // Subscribe to WebSocket live alerts
    const unsubscribe = wsClient.subscribeAlerts((newAlert) => {
      setAlerts((prev) => [newAlert, ...prev]);
      setLiveLog((prev) => [
        { time: new Date().toLocaleTimeString().substring(0, 5), text: `Live Alert: ${newAlert.title}`, type: "ALERT" },
        ...prev.slice(0, 5),
      ]);
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-[#002147]">COMMAND CENTRE DASHBOARD</h1>
            <span className="rounded bg-[#e2f1f8] px-2 py-0.5 text-xs font-extrabold text-[#0077b6] border border-[#bde0fe]">
              GUJARAT POLICE HQ
            </span>
            <span className="rounded bg-amber-50 px-2 py-0.5 text-[10px] font-extrabold text-amber-800 border border-amber-200">
              DEMO DATA
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-600 font-medium">
            Statewide CCTV Intelligence, Real-time AI Event Correlation & Smart Incident Response
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/cameras"
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-extrabold text-slate-700 shadow-sm hover:border-[#0077b6] transition-colors"
          >
            <Video className="h-4 w-4 text-[#0077b6]" />
            <span>Video Wall</span>
          </Link>
          <Link
            href="/alerts"
            className="flex items-center gap-1.5 rounded-lg bg-[#e11d48] px-3.5 py-2 text-xs font-black text-white shadow hover:bg-rose-700 transition-colors"
          >
            <Bell className="h-4 w-4" />
            <span>Alerts ({alerts.length})</span>
          </Link>
        </div>
      </div>

      {/* TOP KPI ROW (5 Column Grid) */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          title="CAMERAS ONLINE"
          value={`${summary?.online_cameras ?? 1231} / ${summary?.total_cameras ?? 1248}`}
          subtitle={`${summary?.degraded_cameras ?? 1} camera degraded`}
          icon={Video}
          badge="98.6% ONLINE"
          badgeColor="green"
        />
        <StatCard
          title="ACTIVE ALERTS"
          value={alerts.filter((a) => a.status === "OPEN" || a.status === "ACKNOWLEDGED").length || 17}
          subtitle={`${alerts.filter((a) => a.severity === "CRITICAL").length || 3} Critical priority`}
          icon={ShieldAlert}
          badge={`${alerts.filter((a) => a.severity === "CRITICAL").length || 3} CRITICAL`}
          badgeColor="red"
        />
        <StatCard
          title="AI EVENTS TODAY"
          value={(summary?.ai_events_today ?? 3842).toLocaleString()}
          subtitle="Real-time object & ANPR inference"
          icon={Cpu}
          badge="REAL-TIME"
          badgeColor="blue"
        />
        <StatCard
          title="VEHICLES TRACKED"
          value={summary?.vehicles_detected_today ?? 928}
          subtitle="ANPR Plates searched on watchlists"
          icon={Car}
          badge="ANPR ACTIVE"
          badgeColor="amber"
        />
        <StatCard
          title="SYSTEM UPTIME"
          value="99.98%"
          subtitle="Zero lost video frames"
          icon={Server}
          badge="HEALTHY"
          badgeColor="green"
        />
      </div>

      {/* MAIN 60/40 SPLIT LAYOUT */}
      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        {/* Left ~60%: GIS Operational Map */}
        <section className="flex flex-col rounded-2xl border border-[#cbd5e1] bg-white p-4 shadow-sm min-h-[520px]">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                <span>OPERATIONAL GIS SITUATIONAL MAP</span>
                <span className="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-extrabold text-emerald-800 border border-emerald-200">
                  LIVE GIS NODES
                </span>
              </h2>
              <p className="text-xs text-slate-500">Integrated CCTV camera locations, vehicle sightings & incident markers</p>
            </div>
            <Link href="/map" className="flex items-center gap-1 text-xs font-bold text-[#0077b6] hover:underline">
              <span>Fullscreen Map</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="flex-1 w-full rounded-xl overflow-hidden border border-slate-200">
            <OperationalMap cameras={cameras.length ? cameras : MOCK_CAMERAS} alerts={alerts.length ? alerts : MOCK_ALERTS} />
          </div>
        </section>

        {/* Right ~40%: Smart Alerts Feed */}
        <aside className="space-y-6">
          <div className="rounded-2xl border border-[#cbd5e1] bg-white p-4 shadow-sm h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3 border-b border-slate-200 pb-3">
                <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                  <Bell className="h-4 w-4 text-rose-600" />
                  <span>SMART ALERTS FEED</span>
                </h2>
                <Link href="/alerts" className="text-xs font-extrabold text-[#0077b6] hover:underline">
                  View All →
                </Link>
              </div>

              <div className="space-y-2.5 max-h-[440px] overflow-y-auto pr-1">
                {(alerts.length ? alerts : MOCK_ALERTS).slice(0, 6).map((alert) => (
                  <Link
                    key={alert.id}
                    href={`/alerts`}
                    className="block rounded-xl border border-slate-200 bg-[#f8fafc] p-3 hover:border-[#0077b6] hover:bg-[#e2f1f8]/50 transition-all shadow-xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-bold text-xs text-slate-800 line-clamp-1">{alert.title}</span>
                      <SeverityBadge severity={alert.severity} />
                    </div>
                    <p className="mt-1 text-[11px] text-slate-600 line-clamp-2">{alert.description}</p>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                      <span className="font-mono text-[#0077b6] font-bold">{alert.camera_code || "CAM-GJ01-001"}</span>
                      <StatusBadge status={alert.status} />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* BOTTOM OPERATIONAL PANELS */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* PANEL 1: Live Camera Health */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
          <h3 className="font-extrabold text-[#002147] text-sm flex items-center justify-between">
            <span>LIVE CAMERA HEALTH</span>
            <span className="text-[10px] font-bold text-[#0077b6]">1,248 NODES</span>
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between rounded-lg bg-[#f8fafc] p-2.5 border border-slate-200">
              <span className="text-slate-700 font-bold flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" /> Online Cameras
              </span>
              <span className="font-black text-emerald-700">1,231 Nodes</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-[#f8fafc] p-2.5 border border-slate-200">
              <span className="text-slate-700 font-bold flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> Degraded Stream / Low FPS
              </span>
              <span className="font-black text-amber-700">14 Nodes</span>
            </div>
            <div className="flex items-center justify-between rounded-lg bg-[#f8fafc] p-2.5 border border-slate-200">
              <span className="text-slate-700 font-bold flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-rose-500" /> Offline / No Signal
              </span>
              <span className="font-black text-rose-700">3 Nodes</span>
            </div>
          </div>
        </div>

        {/* PANEL 2: AI Detections Activity */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
          <h3 className="font-extrabold text-[#002147] text-sm flex items-center justify-between">
            <span>AI INFERENCE BREAKDOWN</span>
            <span className="text-[10px] font-bold text-emerald-700">YOLOv8 + ANPR</span>
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center text-slate-700 font-medium">
              <span>Persons Detected</span>
              <span className="font-mono font-bold text-[#002147]">2,140 (55.7%)</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div className="h-full bg-[#0077b6]" style={{ width: "55.7%" }} />
            </div>

            <div className="flex justify-between items-center text-slate-700 font-medium pt-1">
              <span>Vehicles Tracked</span>
              <span className="font-mono font-bold text-[#002147]">1,210 (31.5%)</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div className="h-full bg-[#10b981]" style={{ width: "31.5%" }} />
            </div>

            <div className="flex justify-between items-center text-slate-700 font-medium pt-1">
              <span>ANPR License Plates</span>
              <span className="font-mono font-bold text-[#002147]">492 (12.8%)</span>
            </div>
            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div className="h-full bg-[#f59e0b]" style={{ width: "12.8%" }} />
            </div>
          </div>
        </div>

        {/* PANEL 3: Recent Operations Timeline */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
          <h3 className="font-extrabold text-[#002147] text-sm flex items-center justify-between">
            <span>RECENT OPERATIONS TIMELINE</span>
            <Clock className="h-3.5 w-3.5 text-slate-500" />
          </h3>
          <div className="space-y-2 text-xs">
            {liveLog.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[11px]">
                <span className="font-mono text-[#0077b6] font-extrabold shrink-0">{log.time}</span>
                <span className="text-slate-700 font-medium line-clamp-1">{log.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
