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

  useEffect(() => {
    handleSearch("GJ05CD5678");
  }, []);

  const handleSearch = async (plate: string) => {
    if (!plate.trim()) return;
    setLoading(true);
    try {
      const result = await api.getVehicleIntelligence(plate.trim());
      setData(result);
    } catch {
      // Handled by api fallback
    } finally {
      setLoading(false);
    }
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

      {data && (
        <div className="space-y-6">
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
