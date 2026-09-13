"use client";

import React, { useState, useEffect } from "react";
import { VehicleIntelligence } from "@/lib/types";
import { api } from "@/lib/api";
import { OperationalMap } from "@/components/map/OperationalMap";
import { Car, Search, ShieldCheck, MapPin, Calendar, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

export default function VehiclesPage() {
  const [plateInput, setPlateInput] = useState("GJ05CD5678");
  const [data, setData] = useState<VehicleIntelligence | null>(null);
  const [loading, setLoading] = useState(false);
  const [fromTime, setFromTime] = useState("");
  const [toTime, setToTime] = useState("");
  const [deletedVehicles, setDeletedVehicles] = useState<Array<{ id: string; plate: string; deleted_at: string | null }>>([]);

  useEffect(() => {
    handleSearch("GJ05CD5678");
  }, []);

  const handleSearch = async (plate: string) => {
    if (!plate.trim()) return;
    setLoading(true);
    try {
      const result = await api.getVehicleIntelligence(plate.trim(), fromTime || undefined, toTime || undefined);
      setData(result);
    } catch {
      // Handled by api fallback
    } finally {
      setLoading(false);
    }
  };

  const loadDeleted = async () => {
    try { setDeletedVehicles(await api.getDeletedVehicles()); } catch { setDeletedVehicles([]); }
  };

  const routePoints = (data?.sightings || []).map((s, idx) => ({
    lat: s.latitude || 23.0225,
    lng: s.longitude || 72.5714,
    label: s.camera_name || `Stop ${idx + 1}`,
  }));

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Car className="h-6 w-6 text-[#0077b6]" />
            <span>ANPR VEHICLE INTELLIGENCE & TRACKING</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">ANPR Plate Search, CCTV Trajectory Analysis & VAHAN Database Lookup</p>
        </div>

        {/* Search Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch(plateInput);
          }}
          className="flex items-center gap-2"
        >
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={plateInput}
              onChange={(e) => setPlateInput(e.target.value)}
              placeholder="Enter Plate # (e.g. GJ05CD5678)..."
              className="w-64 rounded-lg border border-slate-300 bg-slate-50 pl-9 pr-4 py-2 text-xs font-mono font-bold text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white transition-colors shadow-xs"
          >
            {loading ? "Searching ANPR..." : "Run ANPR Track"}
          </button>
        </form>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
        <label className="text-[11px] font-bold text-slate-600">From date/time<input type="datetime-local" value={fromTime} onChange={(e) => setFromTime(e.target.value)} className="mt-1 block rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs" /></label>
        <label className="text-[11px] font-bold text-slate-600">To date/time<input type="datetime-local" value={toTime} onChange={(e) => setToTime(e.target.value)} className="mt-1 block rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs" /></label>
        <button type="button" onClick={() => handleSearch(plateInput)} className="rounded-lg bg-[#0077b6] px-3 py-2 text-xs font-bold text-white">Apply time filter</button>
        <button type="button" onClick={loadDeleted} className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-bold text-slate-700">Deleted records</button>
      </div>

      {deletedVehicles.length > 0 && <div className="rounded-xl border border-amber-200 bg-amber-50 p-4"><h2 className="text-sm font-black text-amber-900">Deleted vehicle records</h2><div className="mt-2 space-y-1 text-xs text-amber-900">{deletedVehicles.map((vehicle) => <div key={vehicle.id} className="flex justify-between"><span className="font-mono font-bold">{vehicle.plate}</span><span>{vehicle.deleted_at ? new Date(vehicle.deleted_at).toLocaleString() : "Unknown time"}</span></div>)}</div></div>}

      {data && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#bde0fe] bg-[#f4fbfe] p-5 shadow-sm">
            <h2 className="flex items-center gap-2 text-sm font-black text-[#002147]"><ShieldCheck className="h-4 w-4 text-[#0077b6]" /> Structured Vehicle Fingerprint</h2>
            <p className="mt-1 text-xs text-slate-600">Persistent appearance, plate, observation, and matching data for authorized search.</p>
            <div className="mt-4 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(data.metadata_json || {}).filter(([key]) => key !== "match_scores").map(([key, value]) => <div key={key} className="rounded-lg border border-slate-200 bg-white p-3"><span className="block text-[10px] font-black uppercase text-slate-500">{key.replaceAll("_", " ")}</span><span className="mt-1 block break-words font-bold text-[#002147]">{typeof value === "object" ? JSON.stringify(value) : String(value)}</span></div>)}
            </div>
            {data.match_scores && <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs"><span className="font-black text-emerald-900">MULTI-FACTOR MATCH SCORES</span><div className="mt-2 flex flex-wrap gap-3">{Object.entries(data.match_scores).map(([key, value]) => <span key={key} className="font-bold text-emerald-800">{key.replaceAll("_", " ")}: {Math.round(value * 100)}%</span>)}</div></div>}
          </div>
          {/* Top Intelligence Summary Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm">
              <span className="text-[10px] font-extrabold uppercase text-slate-500">LICENSE PLATE</span>
              <p className="font-mono text-2xl font-black text-[#0077b6] mt-1">{data.plate}</p>
              <span className="text-xs text-slate-600 font-medium">Normalized: {data.normalized_plate}</span>
            </div>

            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm">
              <span className="text-[10px] font-extrabold uppercase text-slate-500">VEHICLE CLASSIFICATION</span>
              <p className="font-extrabold text-[#002147] text-lg mt-1">{data.vehicle_type || "Automobile"}</p>
              <span className="text-xs text-slate-600 font-medium">Color: {data.color || "Silver"}</span>
            </div>

            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm">
              <span className="text-[10px] font-extrabold uppercase text-slate-500">TOTAL SIGHTINGS</span>
              <p className="font-black text-[#002147] text-2xl mt-1">{data.total_sightings}</p>
              <span className="text-xs text-slate-600 font-medium">Across {data.sightings.length} Cameras</span>
            </div>

            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
              <span className="text-[10px] font-black uppercase text-rose-800">WATCHLIST FLAG</span>
              <p className="font-black text-rose-900 text-lg mt-1">
                {data.watchlist_matches.length ? "FLAGGED (STOLEN)" : "NO ACTIVE FLAGS"}
              </p>
              <span className="text-xs text-rose-700 font-medium">VAHAN FIR Match Confirmed</span>
            </div>
          </div>

          {/* Cross-Camera Vehicle Journey Flow */}
          <div className="rounded-2xl border border-[#0077b6] bg-[#002147] p-5 text-white shadow-md">
            <div className="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-[#64dfdf]">CROSS-CAMERA JOURNEY CORRELATION</span>
                <h2 className="text-base font-black text-white">OBSERVED VEHICLE ROUTE TIMELINE</h2>
              </div>
              <span className="rounded bg-[#00a896] px-3 py-1 text-xs font-black uppercase text-white shadow">
                {data.sightings.length} OBSERVED STOPS
              </span>
            </div>

            <div className="flex items-center gap-3 overflow-x-auto py-2">
              {Array.from(data.sightings).reverse().map((sighting, idx, arr) => (
                <React.Fragment key={sighting.id || idx}>
                  <div className="flex shrink-0 flex-col rounded-xl border border-sky-400/40 bg-sky-950/60 p-3 min-w-[170px] space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono font-bold text-[#64dfdf]">STOP #{idx + 1}</span>
                      <span className="text-[10px] font-black text-emerald-400">{Math.round(sighting.confidence * 100)}% Match</span>
                    </div>
                    <strong className="block text-xs font-bold text-white truncate">{sighting.camera_name || "Camera Node"}</strong>
                    <span className="block text-[10px] text-slate-300 font-mono">
                      {new Date(sighting.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                  {idx < arr.length - 1 && (
                    <div className="flex items-center text-sky-300 shrink-0 px-1">
                      <ArrowRight className="h-5 w-5 animate-pulse" />
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Main Grid: Sightings Timeline & Trajectory Map */}
          <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
            {/* Trajectory Map */}
            <div className="flex flex-col rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 min-h-[480px] shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-[#0077b6]" />
                  <span>Reconstructed CCTV Trajectory</span>
                </h2>
                <span className="text-xs font-mono font-bold text-[#059669]">CHRONOLOGICAL POLYLINE</span>
              </div>
              <div className="flex-1 w-full rounded-xl overflow-hidden border border-slate-200">
                <OperationalMap cameras={[]} vehicleRoute={{ plate: data.plate, points: routePoints }} />
              </div>
            </div>

            {/* Right Column: Registered Owner & Sightings Feed */}
            <div className="space-y-6">
              {/* Authorized VAHAN Record */}
              <div className="rounded-2xl border border-[#bde0fe] bg-[#e2f1f8] p-5 space-y-3 shadow-sm">
                <div className="flex items-center gap-2 border-b border-[#bde0fe] pb-2.5">
                  <ShieldCheck className="h-5 w-5 text-[#0077b6]" />
                  <h2 className="font-extrabold text-[#002147] text-sm">Authorized VAHAN Database Record</h2>
                </div>
                {data.registered_owner ? (
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-600 block text-[10px] font-extrabold uppercase">Registered Owner</span>
                      <strong className="text-[#002147] font-bold text-sm">{data.registered_owner.owner_name}</strong>
                    </div>
                    <div>
                      <span className="text-slate-600 block text-[10px] font-extrabold uppercase">RTO Registration Authority</span>
                      <strong className="text-slate-800 font-bold">{data.registered_owner.rto_location}</strong>
                    </div>
                    <div>
                      <span className="text-slate-600 block text-[10px] font-extrabold uppercase">FIR Stolen Flag</span>
                      <span className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-black text-rose-800 border border-rose-300">
                        {data.registered_owner.stolen_status}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-600">No authorized record matching this plate query.</p>
                )}
              </div>

              {/* Sightings Feed List */}
              <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
                <h2 className="font-extrabold text-[#002147] text-sm">Sightings Chronology</h2>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {data.sightings.map((s, idx) => (
                    <div key={s.id} className="rounded-xl border border-slate-200 bg-[#f8fafc] p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between font-bold">
                        <span className="text-[#002147]">
                          #{idx + 1} {s.camera_name}
                        </span>
                        <span className="text-emerald-700 font-mono font-bold">{Math.round(s.confidence * 100)}% Match</span>
                      </div>
                      <p className="text-slate-600 text-[11px]">Time: {new Date(s.timestamp).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
