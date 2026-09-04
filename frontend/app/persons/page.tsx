"use client";

import React, { useState } from "react";
import { UserCheck, Search, ShieldAlert, Eye, Clock, MapPin } from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";

interface PersonTrack {
  id: string;
  track_code: string;
  first_observed: string;
  last_observed: string;
  cameras_count: number;
  last_camera: string;
  zone: string;
  match_status: "ANONYMOUS" | "POSSIBLE_MATCH" | "VERIFIED";
  confidence: number;
  matched_ref?: string;
  thumbnail: string;
}

const MOCK_PERSONS: PersonTrack[] = [
  {
    id: "p-1",
    track_code: "P-2048",
    first_observed: new Date(Date.now() - 3600000 * 3).toLocaleTimeString(),
    last_observed: new Date(Date.now() - 60000 * 12).toLocaleTimeString(),
    cameras_count: 3,
    last_camera: "Kalupur Station Entrance (CAM-GJ01-003)",
    zone: "Ahmedabad East",
    match_status: "POSSIBLE_MATCH",
    confidence: 0.88,
    matched_ref: "POI-2026-REF-0912",
    thumbnail: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80",
  },
  {
    id: "p-2",
    track_code: "P-3109",
    first_observed: new Date(Date.now() - 3600000 * 5).toLocaleTimeString(),
    last_observed: new Date(Date.now() - 60000 * 45).toLocaleTimeString(),
    cameras_count: 2,
    last_camera: "Ring Road Junction North (CAM-GJ01-001)",
    zone: "Ahmedabad Central",
    match_status: "ANONYMOUS",
    confidence: 0.74,
    thumbnail: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80",
  },
  {
    id: "p-3",
    track_code: "P-4401",
    first_observed: new Date(Date.now() - 3600000 * 1).toLocaleTimeString(),
    last_observed: new Date(Date.now() - 60000 * 5).toLocaleTimeString(),
    cameras_count: 4,
    last_camera: "Sector 11 Secretariat Plaza (CAM-GJ18-001)",
    zone: "Gandhinagar Govt Complex",
    match_status: "POSSIBLE_MATCH",
    confidence: 0.92,
    matched_ref: "POI-2026-REF-0418",
    thumbnail: "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=400&q=80",
  },
];

export default function PersonsIntelligencePage() {
  const [search, setSearch] = useState("");
  const [selectedTrack, setSelectedTrack] = useState<PersonTrack>(MOCK_PERSONS[0]);

  const filtered = MOCK_PERSONS.filter(
    (p) =>
      p.track_code.toLowerCase().includes(search.toLowerCase()) ||
      p.last_camera.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <UserCheck className="h-6 w-6 text-[#0077b6]" />
            <span>PERSON INTELLIGENCE & TRACKING</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">
            Privacy-Conscious Anonymous Track Analysis & Authorized Reference Watchlist Correlation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full bg-[#e2f1f8] px-3 py-1 text-xs font-black text-[#0077b6] border border-[#bde0fe] shadow-xs">
            PRIVACY SAFEGUARDS ACTIVE
          </span>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Track Code (e.g. P-2048), Camera..."
              className="w-full rounded-lg border border-slate-300 bg-slate-50 pl-9 pr-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
            />
          </div>

          <div className="space-y-3">
            {filtered.map((person) => (
              <div
                key={person.id}
                onClick={() => setSelectedTrack(person)}
                className={`cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-2xl border transition-all shadow-sm ${
                  selectedTrack.id === person.id
                    ? "border-[#0077b6] bg-[#e2f1f8]/60 shadow-md"
                    : "border-[#cbd5e1] bg-white hover:border-[#0077b6]"
                }`}
              >
                <div className="flex items-center gap-4">
                  <img
                    src={person.thumbnail}
                    alt={person.track_code}
                    className="h-12 w-12 rounded-xl object-cover border border-slate-300 shrink-0"
                  />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-black text-[#0077b6]">{person.track_code}</span>
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-extrabold ${
                          person.match_status === "POSSIBLE_MATCH"
                            ? "bg-amber-100 text-amber-800 border border-amber-300"
                            : "bg-slate-100 text-slate-700 border border-slate-300"
                        }`}
                      >
                        {person.match_status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-800 font-bold">{person.last_camera}</p>
                    <p className="text-[11px] text-slate-600 font-medium">
                      Observed at {person.cameras_count} camera locations • Confidence:{" "}
                      <strong className="text-emerald-700">{Math.round(person.confidence * 100)}%</strong>
                    </p>
                  </div>
                </div>

                <div className="mt-2 sm:mt-0 text-right text-xs text-slate-600 font-medium">
                  <p className="text-[10px] text-slate-500 uppercase font-extrabold">Last Observed</p>
                  <p className="font-mono font-extrabold text-[#002147]">{person.last_observed}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Detail Card */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 space-y-5 h-fit shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <h2 className="font-extrabold text-[#002147] text-base flex items-center gap-2">
              <Eye className="h-5 w-5 text-[#0077b6]" />
              <span>Track Detail: {selectedTrack.track_code}</span>
            </h2>
          </div>

          <div className="flex items-center gap-4">
            <img
              src={selectedTrack.thumbnail}
              alt={selectedTrack.track_code}
              className="h-20 w-20 rounded-xl object-cover border border-slate-300 shrink-0"
            />
            <div className="space-y-1">
              <p className="text-xs text-slate-500 font-medium">Track Reference ID</p>
              <p className="font-mono font-black text-[#0077b6] text-lg">{selectedTrack.track_code}</p>
              <div className="pt-1">
                <span className="rounded bg-[#e2f1f8] text-[#0077b6] border border-[#bde0fe] px-2 py-0.5 text-[10px] font-extrabold">
                  MATCH CONFIDENCE: {Math.round(selectedTrack.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3 rounded-xl bg-[#f8fafc] border border-slate-200 p-3.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-600 font-medium">Match Status:</span>
              <span className="font-extrabold text-amber-800">{selectedTrack.match_status}</span>
            </div>
            {selectedTrack.matched_ref && (
              <div className="flex justify-between">
                <span className="text-slate-600 font-medium">Watchlist Ref:</span>
                <span className="font-mono text-[#0077b6] font-bold">{selectedTrack.matched_ref}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-600 font-medium">First Observed:</span>
              <span className="text-[#002147] font-mono font-bold">{selectedTrack.first_observed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600 font-medium">Last Observed:</span>
              <span className="text-[#002147] font-mono font-bold">{selectedTrack.last_observed}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600 font-medium">Primary Zone:</span>
              <span className="text-[#002147] font-bold">{selectedTrack.zone}</span>
            </div>
          </div>

          <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-[11px] text-amber-900 font-medium leading-relaxed">
            <strong>PRIVACY NOTICE:</strong> Probabilistic AI detection match. Requires officer verification before official action.
          </div>
        </div>
      </div>
    </div>
  );
}
