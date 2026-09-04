"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Camera } from "@/lib/types";
import { api, MOCK_CAMERAS } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LiveStreamPlayer } from "@/components/video/LiveStreamPlayer";
import { Video, Filter, Search, Eye, Grid, List, RefreshCw, Layers } from "lucide-react";

export default function CamerasPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [zoneFilter, setZoneFilter] = useState<string>("ALL");
  const [search, setSearch] = useState("");
  const [gridLayout, setGridLayout] = useState<"2x2" | "3x3" | "4x4" | "LIST">("3x3");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCameras();
  }, [statusFilter, zoneFilter]);

  const loadCameras = async () => {
    setLoading(true);
    try {
      const data = await api.getCameras(
        statusFilter === "ALL" ? undefined : statusFilter,
        zoneFilter === "ALL" ? undefined : zoneFilter
      );
      setCameras(data.length ? data : MOCK_CAMERAS);
    } catch {
      setCameras(MOCK_CAMERAS);
    } finally {
      setLoading(false);
    }
  };

  const filtered = cameras.filter((c) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.camera_code.toLowerCase().includes(q) ||
        (c.zone && c.zone.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getGridColsClass = () => {
    switch (gridLayout) {
      case "2x2":
        return "grid gap-6 md:grid-cols-2";
      case "3x3":
        return "grid gap-6 md:grid-cols-2 lg:grid-cols-3";
      case "4x4":
        return "grid gap-4 md:grid-cols-2 lg:grid-cols-4";
      default:
        return "grid gap-6 md:grid-cols-3";
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Video className="h-6 w-6 text-[#0077b6]" />
            <span>CCTV VIDEO WALL & CAMERA REGISTRY</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">
            Integrated Video Management System (VMS) & Real-time AI Stream Analysis
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Grid Layout Selector */}
          <div className="flex items-center rounded-lg border border-slate-300 bg-white p-1 text-xs font-extrabold shadow-xs">
            <button
              onClick={() => setGridLayout("2x2")}
              className={`px-2.5 py-1 rounded ${gridLayout === "2x2" ? "bg-[#0077b6] text-white" : "text-slate-600 hover:text-[#002147]"}`}
            >
              2×2
            </button>
            <button
              onClick={() => setGridLayout("3x3")}
              className={`px-2.5 py-1 rounded ${gridLayout === "3x3" ? "bg-[#0077b6] text-white" : "text-slate-600 hover:text-[#002147]"}`}
            >
              3×3
            </button>
            <button
              onClick={() => setGridLayout("4x4")}
              className={`px-2.5 py-1 rounded ${gridLayout === "4x4" ? "bg-[#0077b6] text-white" : "text-slate-600 hover:text-[#002147]"}`}
            >
              4×4
            </button>
            <button
              onClick={() => setGridLayout("LIST")}
              className={`p-1.5 rounded ${gridLayout === "LIST" ? "bg-[#0077b6] text-white" : "text-slate-600 hover:text-[#002147]"}`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>

          <button
            onClick={() => loadCameras()}
            className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-extrabold text-slate-700 hover:bg-slate-50 shadow-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
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
              placeholder="Search camera code, name, zone..."
              className="rounded-lg border border-slate-300 bg-slate-50 pl-9 pr-4 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-500" />
            <span className="text-slate-600 font-extrabold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="ONLINE">ONLINE</option>
              <option value="DEGRADED">DEGRADED</option>
              <option value="OFFLINE">OFFLINE</option>
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-600 font-medium">
          Showing <span className="font-extrabold text-[#002147]">{filtered.length}</span> of {cameras.length} cameras
        </div>
      </div>

      {/* Video Wall Grid View */}
      {gridLayout !== "LIST" ? (
        <div className={getGridColsClass()}>
          {filtered.map((camera) => (
            <div key={camera.id} className="flex flex-col rounded-2xl border border-[#cbd5e1] bg-white overflow-hidden shadow-sm hover:border-[#0077b6] transition-all">
              <LiveStreamPlayer camera={camera} showOverlayDefault={true} />
              <div className="p-4 flex flex-col justify-between flex-1 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <Link href={`/cameras/${camera.id}`} className="font-extrabold text-sm text-[#002147] hover:text-[#0077b6] transition-colors">
                      {camera.name}
                    </Link>
                    <p className="text-xs text-slate-600 mt-0.5 font-medium">{camera.description || "State Surveillance Node"}</p>
                  </div>
                  <StatusBadge status={camera.status} />
                </div>

                <div className="flex items-center justify-between text-xs text-slate-600 pt-2.5 border-t border-slate-200">
                  <span>Type: <strong className="text-[#002147] font-bold">{camera.camera_type}</strong></span>
                  <Link
                    href={`/cameras/${camera.id}`}
                    className="flex items-center gap-1 font-extrabold text-[#0077b6] hover:underline"
                  >
                    <Eye className="h-3.5 w-3.5" /> Full Detail View
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* List View */
        <div className="overflow-hidden rounded-2xl border border-[#cbd5e1] bg-white shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-300 bg-[#f8fafc] text-slate-600 font-extrabold uppercase tracking-wider">
              <tr>
                <th className="p-3.5">Camera Code</th>
                <th className="p-3.5">Name</th>
                <th className="p-3.5">Zone</th>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Protocol</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-slate-700">
              {filtered.map((c) => (
                <tr key={c.id} className="hover:bg-[#e2f1f8]/40 transition-colors">
                  <td className="p-3.5 font-mono font-black text-[#0077b6]">{c.camera_code}</td>
                  <td className="p-3.5 font-extrabold text-[#002147]">{c.name}</td>
                  <td className="p-3.5 font-medium">{c.zone}</td>
                  <td className="p-3.5">{c.camera_type}</td>
                  <td className="p-3.5">{c.protocol}</td>
                  <td className="p-3.5"><StatusBadge status={c.status} /></td>
                  <td className="p-3.5 text-right">
                    <Link
                      href={`/cameras/${c.id}`}
                      className="rounded-lg bg-[#0077b6] px-3 py-1.5 font-extrabold text-white hover:bg-[#005b8e] shadow-xs"
                    >
                      View Stream
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
