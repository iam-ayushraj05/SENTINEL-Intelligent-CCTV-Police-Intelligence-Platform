"use client";

import React, { useEffect, useState } from "react";
import { Watchlist, WatchlistEntry } from "@/lib/types";
import { api, MOCK_WATCHLISTS, MOCK_WATCHLIST_ENTRIES } from "@/lib/api";
import { Eye, Plus, Trash2, ShieldAlert, CheckCircle2, Search } from "lucide-react";

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedWl, setSelectedWl] = useState<Watchlist | null>(null);
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [refInput, setRefInput] = useState("");
  const [priorityInput, setPriorityInput] = useState("HIGH");
  const [sourceInput, setSourceInput] = useState("VAHAN_POLICE_FIR");

  useEffect(() => {
    loadWatchlists();
  }, []);

  const loadWatchlists = async () => {
    try {
      const data = await api.getWatchlists();
      const list = data.length ? data : MOCK_WATCHLISTS;
      setWatchlists(list);
      if (list[0]) {
        selectWatchlist(list[0]);
      }
    } catch {
      setWatchlists(MOCK_WATCHLISTS);
      selectWatchlist(MOCK_WATCHLISTS[0]);
    }
  };

  const selectWatchlist = async (wl: Watchlist) => {
    setSelectedWl(wl);
    try {
      const eData = await api.getWatchlistEntries(wl.id);
      setEntries(eData.length ? eData : MOCK_WATCHLIST_ENTRIES);
    } catch {
      setEntries(MOCK_WATCHLIST_ENTRIES);
    }
  };

  const handleAddEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWl || !refInput.trim()) return;

    const normalized = refInput.replace(/[^A-Z0-9]/gi, "").toUpperCase();
    try {
      const newE = await api.addWatchlistEntry(selectedWl.id, {
        subject_reference: refInput.trim(),
        priority: priorityInput,
        source_system: sourceInput,
      });
      setEntries([newE, ...entries]);
    } catch {
      const fallbackE = {
        id: `wle-${Date.now()}`,
        watchlist_id: selectedWl.id,
        subject_reference: refInput.trim(),
        normalized_reference: normalized,
        priority: priorityInput,
        source_system: sourceInput,
        active: true,
        created_at: new Date().toISOString(),
      };
      setEntries([fallbackE, ...entries]);
    } finally {
      setShowAddModal(false);
      setRefInput("");
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Eye className="h-6 w-6 text-[#0077b6]" />
            <span>AUTHORIZED WATCHLISTS MANAGEMENT</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">Statewide Target Reference Lists for Real-time ANPR & AI Correlation</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white shadow-xs transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Add Flagged Entry</span>
        </button>
      </div>

      {/* Grid Layout */}
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        {/* Watchlist Selectors */}
        <aside className="space-y-3">
          <p className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">AUTHORIZED WATCHLISTS</p>
          <div className="space-y-2">
            {watchlists.map((wl) => {
              const isSelected = selectedWl?.id === wl.id;
              return (
                <div
                  key={wl.id}
                  onClick={() => selectWatchlist(wl)}
                  className={`cursor-pointer rounded-2xl border p-4 transition-all shadow-sm ${
                    isSelected
                      ? "border-[#0077b6] bg-[#e2f1f8]/70 shadow-md"
                      : "border-[#cbd5e1] bg-white hover:border-[#0077b6]"
                  }`}
                >
                  <h2 className="font-extrabold text-xs text-[#002147]">{wl.name}</h2>
                  <p className="text-[11px] text-slate-600 font-medium mt-1">{wl.description}</p>
                  <div className="mt-3 flex items-center justify-between text-[10px]">
                    <span className="font-mono text-[#0077b6] font-bold">{wl.entity_type}</span>
                    <span className="rounded bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 text-emerald-800 font-bold">{wl.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Entries Table */}
        <main className="space-y-4">
          <div className="rounded-2xl border border-[#cbd5e1] bg-white overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="font-extrabold text-[#002147] text-sm">{selectedWl?.name || "Active Watchlist"}</h2>
                <p className="text-xs text-slate-600 font-medium">{selectedWl?.description}</p>
              </div>
              <span className="text-xs font-bold text-[#0077b6]">{entries.length} Active Target References</span>
            </div>

            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-300 bg-[#f8fafc] text-slate-600 font-extrabold uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Target Reference</th>
                  <th className="p-3.5">Normalized Code</th>
                  <th className="p-3.5">Source Registry</th>
                  <th className="p-3.5">Alert Priority</th>
                  <th className="p-3.5 text-right">Added On</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700 font-medium">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-[#e2f1f8]/40 transition-colors">
                    <td className="p-3.5 font-mono font-black text-[#0077b6] text-sm">{entry.subject_reference}</td>
                    <td className="p-3.5 font-mono text-slate-500 font-bold">{entry.normalized_reference}</td>
                    <td className="p-3.5 font-extrabold text-[#002147]">{entry.source_system || "STATE_FIR_DB"}</td>
                    <td className="p-3.5">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-extrabold uppercase ${
                          entry.priority === "CRITICAL"
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-amber-50 text-amber-800 border border-amber-200"
                        }`}
                      >
                        {entry.priority}
                      </span>
                    </td>
                    <td className="p-3.5 text-right text-slate-600 font-mono">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 text-slate-800">
          <div className="w-full max-w-md rounded-2xl border border-[#cbd5e1] bg-white p-6 space-y-4 shadow-2xl">
            <h2 className="text-lg font-extrabold text-[#002147]">Add Watchlist Target Reference</h2>
            <form onSubmit={handleAddEntry} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-600 font-extrabold mb-1">Target Reference (Plate / ID)</label>
                <input
                  type="text"
                  value={refInput}
                  onChange={(e) => setRefInput(e.target.value)}
                  required
                  placeholder="e.g. GJ05CD5678"
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-mono text-slate-800 focus:border-[#0077b6] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-extrabold mb-1">Priority</label>
                <select
                  value={priorityInput}
                  onChange={(e) => setPriorityInput(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 font-extrabold mb-1">Source Agency / FIR System</label>
                <input
                  type="text"
                  value={sourceInput}
                  onChange={(e) => setSourceInput(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 font-bold text-slate-700 hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 font-extrabold text-white shadow-xs"
                >
                  Add Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
