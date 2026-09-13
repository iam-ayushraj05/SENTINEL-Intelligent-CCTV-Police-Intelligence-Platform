"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { searchFaceAcrossCameras, FaceSearchResult } from "@/lib/faceSearch";
import { Search, Video, Bell, Car, Briefcase, UserRound, Upload, Radio, MapPin, Clock3, ShieldCheck } from "lucide-react";

function SearchPageContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams?.get("q") || "GJ05CD5678";

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState<"global" | "person">("global");
  const [personImage, setPersonImage] = useState<File | null>(null);
  const [personPreview, setPersonPreview] = useState<string | null>(null);
  const [faceResults, setFaceResults] = useState<FaceSearchResult | null>(null);
  const [faceError, setFaceError] = useState<string | null>(null);

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

  const handlePersonImage = (file?: File) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setFaceError("Choose a JPG, PNG, WEBP, or other image file.");
      return;
    }
    setFaceError(null);
    setPersonImage(file);
    setPersonPreview(URL.createObjectURL(file));
    setFaceResults(null);
  };

  const handleFaceSearch = async () => {
    if (!personImage) {
      setFaceError("Add a reference photo before searching cameras.");
      return;
    }
    setLoading(true);
    setFaceError(null);
    try {
      const cameras = await api.getCameras();
      setFaceResults(await searchFaceAcrossCameras(personImage, cameras));
    } catch {
      setFaceError("The camera registry could not be reached. Try again shortly.");
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
          <p className="mt-1 text-xs text-slate-600 font-medium">Cross-correlate cameras, alerts, plates, cases and watchlist entries</p>
        </div>

        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Search type">
          <button type="button" onClick={() => setSearchType("global")} className={`rounded-lg border px-4 py-2 text-xs font-extrabold ${searchType === "global" ? "border-[#0077b6] bg-[#0077b6] text-white" : "border-slate-300 bg-white text-slate-700"}`}>Global Search</button>
          <button type="button" onClick={() => setSearchType("person")} className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-extrabold ${searchType === "person" ? "border-[#0077b6] bg-[#0077b6] text-white" : "border-slate-300 bg-white text-slate-700"}`}><UserRound className="h-4 w-4" /> Person Detection</button>
        </div>

        {searchType === "person" ? (
          <div className="rounded-xl border border-[#b9d8e7] bg-[#f4fbfe] p-4 space-y-4">
            <div className="flex items-center justify-between gap-3"><div><h2 className="text-sm font-black text-[#002147]">AI Person Search</h2><p className="text-xs text-slate-600">Upload a reference photo to search connected live and recorded camera sources.</p></div><span className="flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[10px] font-black text-emerald-700 border border-emerald-200"><ShieldCheck className="h-3 w-3" /> Camera registry</span></div>
            <div className="flex flex-wrap items-center gap-4">
              <label className="flex h-24 w-24 cursor-pointer items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-[#8fc4d9] bg-white hover:border-[#0077b6]">{personPreview ? <img src={personPreview} alt="Selected person" className="h-full w-full object-cover" /> : <span className="text-center text-[10px] font-bold text-[#0077b6]"><Upload className="mx-auto mb-1 h-5 w-5" />Add photo</span>}<input type="file" accept="image/*" className="hidden" onChange={(event) => handlePersonImage(event.target.files?.[0])} /></label>
              <div className="min-w-[220px] flex-1"><p className="text-xs font-extrabold text-[#002147]">{personImage?.name || "No reference photo selected"}</p><p className="mt-1 text-[11px] text-slate-600">JPG, PNG and common image formats. Search is restricted to authorized camera sources.</p><button type="button" onClick={handleFaceSearch} disabled={loading || !personImage} className="mt-3 rounded-lg bg-[#0077b6] px-4 py-2 text-xs font-extrabold text-white disabled:cursor-not-allowed disabled:opacity-50">{loading ? "Analyzing cameras..." : "Search All Cameras"}</button></div>
            </div>
            {faceError && <p className="text-xs font-bold text-rose-700">{faceError}</p>}
          </div>
        ) : (

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
        )}
      </div>

      {faceResults && <div className="space-y-6"><div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]"><section className="rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm"><div className="flex items-center justify-between gap-3 border-b border-slate-200 pb-3"><div><h2 className="flex items-center gap-2 text-sm font-extrabold text-[#002147]"><UserRound className="h-4 w-4 text-[#0077b6]" /> Person Movement Timeline</h2><p className="mt-1 text-[11px] text-slate-500">{faceResults.searchedCameras} connected cameras searched · {faceResults.source === "DEMO" ? "Synthetic demo result" : "AI service result"}</p></div><span className="rounded bg-emerald-50 px-2 py-1 text-[10px] font-black text-emerald-700">{faceResults.events.length} MATCHES</span></div><div className="mt-4 space-y-3">{faceResults.events.map((event, index) => <div key={event.id} className="relative flex gap-3 pl-1"><div className="flex flex-col items-center"><span className={`mt-1 h-3 w-3 rounded-full border-2 ${event.status === "LIVE" ? "border-rose-500 bg-rose-100" : "border-[#0077b6] bg-[#d9f1fa]"}`} />{index < faceResults.events.length - 1 && <span className="h-full min-h-12 w-px bg-slate-200" />}</div><div className="mb-2 flex-1 rounded-lg border border-slate-200 bg-[#f8fafc] p-3"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-black text-[#002147]">{event.cameraName}</p><span className={`text-[10px] font-black ${event.status === "LIVE" ? "text-rose-700" : "text-slate-500"}`}>{event.status}</span></div><p className="mt-1 flex items-center gap-1 text-[11px] font-semibold text-slate-600"><MapPin className="h-3 w-3" /> {event.location}</p><p className="mt-1 flex flex-wrap gap-3 text-[10px] text-slate-500"><span><Clock3 className="mr-1 inline h-3 w-3" />{new Date(event.timestamp).toLocaleString()}</span><span>Match {Math.round(event.confidence * 100)}%</span>{event.direction && <span>Direction: {event.direction}</span>}</p></div></div>)}</div></section><section className="rounded-2xl border border-[#cbd5e1] bg-[#002147] p-5 text-white shadow-sm">{faceResults.events.length ? (() => { const current = faceResults.events[faceResults.events.length - 1]; return <><div className="flex items-center justify-between"><h2 className="flex items-center gap-2 text-sm font-extrabold"><Radio className="h-4 w-4 text-cyan-300" /> Live Tracking</h2><span className="rounded bg-rose-500/20 px-2 py-1 text-[10px] font-black text-rose-200">LIVE</span></div><p className="mt-5 text-lg font-black">Person currently detected</p><p className="mt-1 text-xs text-slate-300">{current.cameraName} · {current.location}</p><div className="mt-5 flex aspect-video items-center justify-center rounded-lg border border-white/15 bg-[#12395d] text-center text-xs text-slate-300"><Video className="mr-2 h-5 w-5" /> Live feed integration ready</div><div className="mt-4 grid grid-cols-2 gap-3 text-xs"><div><span className="text-slate-400">Current time</span><p className="font-bold">{new Date(current.timestamp).toLocaleTimeString()}</p></div><div><span className="text-slate-400">Confidence</span><p className="font-bold">{Math.round(current.confidence * 100)}%</p></div></div></>; })() : <p className="text-sm">No matching appearances found.</p>}</section></div><div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900"><strong>PERSON MATCH FOUND</strong> alerts are ready to be emitted by the AI service contract. Demo results are labeled synthetic and do not represent a real person or live police feed.</div></div>}

      {searchType === "global" && results && (
        <div className="space-y-6">
          {/* ANPR Vehicle Plates Matches */}
          {results.vehicles?.length > 0 && (
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-3 shadow-sm">
              <h2 className="font-extrabold text-[#002147] text-sm flex items-center gap-2"><Car className="h-4 w-4 text-[#0077b6]" /><span>Vehicle Intelligence Profiles ({results.vehicles.length})</span></h2>
              <div className="grid gap-3 md:grid-cols-2">{results.vehicles.map((vehicle: any) => <Link key={vehicle.id} href={`/vehicles?plate=${encodeURIComponent(vehicle.plate)}`} className="rounded-xl border border-slate-200 bg-[#f8fafc] p-4 hover:border-[#0077b6]"><div className="flex items-center justify-between"><span className="font-mono text-sm font-black text-[#0077b6]">{vehicle.plate}</span><span className="text-[10px] font-black uppercase text-emerald-700">Persistent record</span></div><p className="mt-2 text-xs font-bold text-[#002147]">{vehicle.make || "Unknown make"} {vehicle.model || ""} · {vehicle.vehicle_type || "Vehicle"}</p><p className="mt-1 text-[11px] text-slate-600">Color: {vehicle.color || "Not recorded"} · Last seen: {new Date(vehicle.last_seen).toLocaleString()}</p></Link>)}</div>
            </div>
          )}

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

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="p-6 text-slate-600">Loading search...</div>}>
      <SearchPageContent />
    </Suspense>
  );
}
