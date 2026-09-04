"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Alert } from "@/lib/types";
import { api, MOCK_ALERTS } from "@/lib/api";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ArrowLeft, CheckCircle2, UserPlus, Briefcase, Check, X, ShieldAlert, Camera as CameraIcon, Clock } from "lucide-react";

export default function AlertDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [alert, setAlert] = useState<Alert | null>(null);
  const [officerName, setOfficerName] = useState("Sub-Inspector Rajesh Patel");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.getAlert(id).then((a) => setAlert(a || MOCK_ALERTS[0]));
  }, [id]);

  if (!alert) {
    return <div className="flex min-h-[50vh] items-center justify-center text-xs text-slate-400">Loading Alert Details...</div>;
  }

  const handleAcknowledge = async () => {
    setLoading(true);
    try {
      const updated = await api.acknowledgeAlert(alert.id, officerName);
      setAlert(updated);
    } catch {
      setAlert({ ...alert, status: "ACKNOWLEDGED", assigned_officer: officerName });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvestigation = async () => {
    try {
      const caseObj = await api.createInvestigation({
        title: `Investigation: ${alert.title}`,
        description: `Triggered from Sentinel Alert ${alert.alert_code}. ${alert.description}`,
        assigned_officer_name: officerName,
      });
      router.push(`/investigations/${caseObj.id}`);
    } catch {
      router.push("/investigations");
    }
  };

  const handleResolve = async () => {
    try {
      const updated = await api.resolveAlert(alert.id);
      setAlert(updated);
    } catch {
      setAlert({ ...alert, status: "RESOLVED" });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/alerts"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-indigo-400">{alert.alert_code}</span>
              <SeverityBadge severity={alert.severity} />
              <StatusBadge status={alert.status} />
            </div>
            <h1 className="text-xl font-extrabold text-white mt-0.5">{alert.title}</h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {alert.status === "OPEN" && (
            <button
              onClick={handleAcknowledge}
              disabled={loading}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-500 shadow"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>Acknowledge</span>
            </button>
          )}

          <button
            onClick={handleCreateInvestigation}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-indigo-500 shadow"
          >
            <Briefcase className="h-4 w-4" />
            <span>Convert to Case</span>
          </button>

          {alert.status !== "RESOLVED" && (
            <button
              onClick={handleResolve}
              className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700"
            >
              <Check className="h-4 w-4 text-emerald-400" />
              <span>Resolve Alert</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Evidence & Intelligence Correlation */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column: Evidence Snapshot & Camera details */}
        <div className="space-y-6">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 space-y-3">
            <h2 className="font-bold text-slate-100 text-sm flex items-center justify-between">
              <span>Evidence Frame Snapshot</span>
              <span className="text-[10px] font-mono text-emerald-400">HASH: SHA256-8A19F</span>
            </h2>

            <div className="relative overflow-hidden rounded-lg border border-slate-800 bg-[#050c17]">
              {/* Image Evidence */}
              <img
                src={alert.evidence_url || "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80"}
                alt="Alert Evidence Frame"
                className="w-full h-64 object-cover"
              />
              <div className="absolute top-2 left-2 rounded bg-black/80 px-2 py-1 text-[10px] font-bold text-red-400 border border-red-800">
                MATCHED TARGET: GJ05CD5678
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 space-y-3">
            <h2 className="font-bold text-slate-100 text-sm">Source Camera Metadata</h2>
            <div className="grid gap-2 sm:grid-cols-2 text-xs">
              <div className="rounded bg-[#07111f] p-2.5 border border-slate-800">
                <span className="text-slate-500 uppercase text-[10px] font-bold block">Camera Name</span>
                <span className="font-semibold text-slate-200">{alert.camera_name || "Ring Road Junction North"}</span>
              </div>
              <div className="rounded bg-[#07111f] p-2.5 border border-slate-800">
                <span className="text-slate-500 uppercase text-[10px] font-bold block">Camera Code</span>
                <span className="font-mono text-indigo-300 font-bold">{alert.camera_code || "CAM-GJ01-001"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Watchlist & Government DB Correlation */}
        <div className="space-y-6">
          <div className="rounded-xl border border-amber-800/80 bg-amber-950/30 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-amber-400" />
              <h2 className="font-extrabold text-amber-200 text-sm">Watchlist Match Intelligence</h2>
            </div>
            <p className="text-xs text-amber-300/90 leading-relaxed">
              Target license plate <strong className="font-mono text-white">GJ05CD5678</strong> matched against state watchlist 
              <strong> "Stolen & Crime-Linked Vehicles"</strong>.
            </p>
            <div className="rounded-lg bg-[#07111f] p-3 border border-slate-800 text-xs space-y-1.5">
              <p><span className="text-slate-400">Watchlist Reference:</span> <strong className="text-slate-200">FIR-2026-SURAT-00412</strong></p>
              <p><span className="text-slate-400">Match Confidence:</span> <strong className="text-emerald-400">96.4%</strong></p>
              <p><span className="text-slate-400">Source Agency:</span> <strong className="text-slate-200">Gujarat Police Crime Branch</strong></p>
            </div>
          </div>

          {/* Assigned Officer Panel */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4 space-y-3">
            <h2 className="font-bold text-slate-100 text-sm">Operational Assignment</h2>
            <div className="text-xs space-y-2">
              <p className="text-slate-400">Assigned Response Officer:</p>
              <input
                type="text"
                value={officerName}
                onChange={(e) => setOfficerName(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-[#07111f] px-3 py-2 text-xs text-white"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
