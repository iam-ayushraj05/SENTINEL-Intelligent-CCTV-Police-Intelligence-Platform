"use client";

import React, { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Search, Video, Bell, Car, Briefcase, Eye } from "lucide-react";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams?.get("q") || "GJ05CD5678";

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleSearch = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    try {
      const data = await api.globalSearch(q.trim());
      setResults(data.results || data);
    } catch {
      // Fallback mock search output
      setResults({
        cameras: [
          { id: "cam-1", code: "CAM-GJ01-001", name: "Ring Road Junction North", zone: "Ahmedabad Central", status: "ONLINE" },
        ],
        alerts: [
          { id: "alt-1", code: "ALT-20260904-9981", title: "WATCHLIST MATCH: Stolen Vehicle GJ05CD5678", severity: "CRITICAL", status: "OPEN" },
        ],
        plates: [
          { plate: "GJ05CD5678", confidence: 0.96, camera_id: "cam-1", timestamp: new Date().toISOString() },
        ],
        investigations: [
          { id: "inv-1", case_number: "CASE-2026-GJ-0091", title: "Stolen Bolero Ring Road Case", status: "INVESTIGATING" },
        ],
        watchlists: [
          { id: "wle-1", reference: "GJ05CD5678", priority: "HIGH", source: "VAHAN_POLICE_FIR" },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header & Search Bar */}
      <div className="border-b border-slate-300 pb-4 space-y-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Search className="h-6 w-6 text-[#0077b6]" />
            <span>GLOBAL STATEWIDE SEARCH ENGINE</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">Cross-Correlate Cameras, Alerts, Plates, Cases and Watchlist Entries</p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch(query);
          }}
          className="flex gap-2 max-w-2xl"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search plate number, camera code, alert code, case number..."
              className="w-full rounded-lg border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-5 py-2.5 text-sm font-extrabold text-white transition-colors shadow-xs"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </form>
      </div>

      {results && (
        <div className="space-y-6">
          {/* ANPR Vehicle Plates Matches */}
          {results.plates?.length > 0 && (
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                <Car className="h-4 w-4 text-[#0077b6]" />
                <span>ANPR License Plate Matches ({results.plates.length})</span>
              </h2>
              <div className="grid gap-2 sm:grid-cols-2">
                {results.plates.map((p: any, idx: number) => (
                  <Link
                    key={idx}
                    href={`/vehicles?plate=${p.plate}`}
                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-[#f8fafc] p-3.5 hover:border-[#0077b6] hover:bg-[#e2f1f8]/50 transition-colors"
                  >
                    <div>
                      <span className="font-mono font-black text-[#0077b6] text-sm">{p.plate}</span>
                      <p className="text-[11px] text-slate-600 font-medium">Confidence: {Math.round(p.confidence * 100)}%</p>
                    </div>
                    <span className="text-xs font-extrabold text-[#0077b6]">View ANPR Profile →</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Alerts Matches */}
          {results.alerts?.length > 0 && (
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                <Bell className="h-4 w-4 text-rose-600" />
                <span>Correlated Alerts ({results.alerts.length})</span>
              </h2>
              <div className="space-y-2">
                {results.alerts.map((a: any) => (
                  <Link
                    key={a.id}
                    href={`/alerts`}
                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-[#f8fafc] p-3.5 hover:border-[#0077b6] hover:bg-[#e2f1f8]/50 transition-colors"
                  >
                    <div>
                      <span className="font-mono text-xs font-black text-[#0077b6]">{a.code}</span>
                      <h3 className="font-extrabold text-[#002147] text-xs mt-0.5">{a.title}</h3>
                    </div>
                    <span className="rounded bg-rose-50 px-2 py-0.5 text-[10px] font-black text-rose-700 border border-rose-200">
                      {a.severity}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Cameras Matches */}
          {results.cameras?.length > 0 && (
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                <Video className="h-4 w-4 text-[#0077b6]" />
                <span>Matching CCTV Cameras ({results.cameras.length})</span>
              </h2>
              <div className="grid gap-2 sm:grid-cols-2">
                {results.cameras.map((c: any) => (
                  <Link
                    key={c.id}
                    href={`/cameras/${c.id}`}
                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-[#f8fafc] p-3.5 hover:border-[#0077b6]"
                  >
                    <div>
                      <span className="font-mono text-xs font-black text-[#0077b6]">{c.code}</span>
                      <p className="font-extrabold text-[#002147] text-xs">{c.name}</p>
                    </div>
                    <span className="text-xs font-black text-emerald-700">{c.status}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Investigation Case Files Matches */}
          {results.investigations?.length > 0 && (
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-[#0077b6]" />
                <span>Investigation Cases ({results.investigations.length})</span>
              </h2>
              <div className="space-y-2">
                {results.investigations.map((inv: any) => (
                  <Link
                    key={inv.id}
                    href={`/investigations`}
                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-[#f8fafc] p-3.5 hover:border-[#0077b6]"
                  >
                    <div>
                      <span className="font-mono text-xs font-black text-[#0077b6]">{inv.case_number}</span>
                      <p className="font-extrabold text-[#002147] text-xs">{inv.title}</p>
                    </div>
                    <span className="text-xs font-bold text-slate-700">{inv.status}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
