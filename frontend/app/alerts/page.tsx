"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Alert, Severity, AlertStatus } from "@/lib/types";
import { api, MOCK_ALERTS } from "@/lib/api";
import { wsClient } from "@/lib/ws";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Bell, Filter, Search, CheckCircle2, ShieldAlert, ArrowRight } from "lucide-react";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();

    // Subscribe to WebSocket live alerts
    const unsubscribe = wsClient.subscribeAlerts((newAlert) => {
      setAlerts((prev) => [newAlert, ...prev]);
    });

    return () => unsubscribe();
  }, [severityFilter, statusFilter]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(
        severityFilter === "ALL" ? undefined : severityFilter,
        statusFilter === "ALL" ? undefined : statusFilter
      );
      setAlerts(data.length ? data : MOCK_ALERTS);
    } catch {
      setAlerts(MOCK_ALERTS);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (e: React.MouseEvent, alertId: string) => {
    e.stopPropagation();
    try {
      const updated = await api.acknowledgeAlert(alertId, "Inspector General A. Sharma");
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
    } catch {
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: "ACKNOWLEDGED", assigned_officer: "Inspector General A. Sharma" } : a))
      );
    }
  };

  const filtered = alerts.filter((a) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        a.title.toLowerCase().includes(q) ||
        a.alert_code.toLowerCase().includes(q) ||
        (a.description && a.description.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Bell className="h-6 w-6 text-rose-600" />
            <span>ALERTS & INCIDENT COMMAND CENTER</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">Automated AI Detection Alerts & Database Correlation Incidents</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-black text-rose-700 border border-rose-200 shadow-xs">
            {filtered.filter((a) => a.severity === "CRITICAL").length} CRITICAL ALERTS
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#cbd5e1] bg-white p-3.5 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search alert title, code..."
              className="rounded-lg border border-slate-300 bg-slate-50 pl-9 pr-4 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-600 font-extrabold">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="rounded border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-slate-600 font-extrabold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-600 font-medium">
          Showing <span className="font-extrabold text-[#002147]">{filtered.length}</span> alerts
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filtered.map((alert) => (
          <div
            key={alert.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-[#cbd5e1] bg-white p-4 hover:border-[#0077b6] transition-all shadow-sm"
          >
            <div className="flex items-start gap-3.5">
              <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 border border-slate-200">
                <ShieldAlert className={`h-5 w-5 ${alert.severity === "CRITICAL" ? "text-rose-600" : alert.severity === "HIGH" ? "text-orange-600" : "text-amber-600"}`} />
              </div>
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-black text-[#0077b6]">{alert.alert_code}</span>
                  <SeverityBadge severity={alert.severity} />
                  <StatusBadge status={alert.status} />
                </div>
                <h2 className="font-extrabold text-[#002147] text-sm">{alert.title}</h2>
                <p className="text-xs text-slate-600 font-medium">{alert.description}</p>
                <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1">
                  <span>Camera: <strong className="text-slate-800 font-bold">{alert.camera_name || "Camera System"}</strong></span>
                  <span>Confidence: <strong className="text-emerald-700 font-bold">{Math.round((alert.confidence || 0.95) * 100)}%</strong></span>
                  <span>Time: {new Date(alert.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center">
              {alert.status === "OPEN" && (
                <button
                  onClick={(e) => handleAcknowledge(e, alert.id)}
                  className="flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-extrabold text-emerald-800 hover:bg-emerald-100 transition-colors shadow-xs"
                >
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  <span>Acknowledge</span>
                </button>
              )}
              <Link
                href={`/alerts`}
                className="flex items-center gap-1 rounded-lg bg-[#0077b6] px-4 py-1.5 text-xs font-extrabold text-white hover:bg-[#005b8e] transition-colors shadow-xs"
              >
                <span>Investigate</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
