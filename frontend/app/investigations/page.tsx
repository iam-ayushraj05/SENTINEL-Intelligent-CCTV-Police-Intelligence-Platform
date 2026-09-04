"use client";

import React, { useEffect, useState } from "react";
import { Investigation } from "@/lib/types";
import { api, MOCK_INVESTIGATIONS } from "@/lib/api";
import { Briefcase, Plus, FileText, UserCheck, Clock, ShieldCheck, Image as ImageIcon, Send } from "lucide-react";

export default function InvestigationsPage() {
  const [cases, setCases] = useState<Investigation[]>([]);
  const [selectedCase, setSelectedCase] = useState<Investigation | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newNote, setNewNote] = useState("");

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      const data = await api.getInvestigations();
      const list = data.length ? data : MOCK_INVESTIGATIONS;
      setCases(list);
      setSelectedCase(list[0] || null);
    } catch {
      setCases(MOCK_INVESTIGATIONS);
      setSelectedCase(MOCK_INVESTIGATIONS[0]);
    }
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const created = await api.createInvestigation({
        title: newTitle,
        description: newDesc,
        assigned_officer_name: "Sub-Inspector Rajesh Patel",
      });
      setCases([created, ...cases]);
      setSelectedCase(created);
      setShowCreateModal(false);
      setNewTitle("");
      setNewDesc("");
    } catch {
      setShowCreateModal(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase || !newNote.trim()) return;
    try {
      const noteObj = await api.addInvestigationNote(selectedCase.id, newNote, "Sub-Inspector Rajesh Patel");
      const updatedCase = {
        ...selectedCase,
        notes: [...(selectedCase.notes || []), noteObj],
      };
      setSelectedCase(updatedCase);
      setCases(cases.map((c) => (c.id === updatedCase.id ? updatedCase : c)));
      setNewNote("");
    } catch {
      // Fallback local update
      const fallbackNote = {
        id: `n-${Date.now()}`,
        investigation_id: selectedCase.id,
        author: "Sub-Inspector Rajesh Patel",
        note: newNote,
        created_at: new Date().toISOString(),
      };
      const updatedCase = {
        ...selectedCase,
        notes: [...(selectedCase.notes || []), fallbackNote],
      };
      setSelectedCase(updatedCase);
      setNewNote("");
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-300 pb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-[#0077b6]" />
            <span>INVESTIGATION CASE WORKSPACE</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">Multi-Agency Evidence Vault & Case Timeline Correlation</p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white shadow-xs transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>New Case File</span>
        </button>
      </div>

      {/* Case Grid Layout: Left List, Right Active Case Workspace */}
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* Left Case List */}
        <aside className="space-y-3">
          <p className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">ACTIVE CASE FILES</p>
          <div className="space-y-2 max-h-[700px] overflow-y-auto pr-1">
            {cases.map((c) => {
              const isSelected = selectedCase?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCase(c)}
                  className={`cursor-pointer rounded-2xl border p-4 transition-all shadow-sm ${
                    isSelected
                      ? "border-[#0077b6] bg-[#e2f1f8]/70 shadow-md"
                      : "border-[#cbd5e1] bg-white hover:border-[#0077b6]"
                  }`}
                >
                  <span className="font-mono text-xs font-black text-[#0077b6]">{c.case_number}</span>
                  <h2 className="font-extrabold text-xs text-[#002147] mt-1 line-clamp-1">{c.title}</h2>
                  <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-600 font-medium">
                    <span>Officer: {c.assigned_officer_name || "Unassigned"}</span>
                    <span className="rounded bg-slate-100 px-2 py-0.5 font-bold uppercase text-slate-800 border border-slate-300">{c.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Right Active Case Workspace */}
        {selectedCase ? (
          <main className="space-y-6">
            <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 space-y-4 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
                <div>
                  <span className="font-mono text-xs font-black text-[#0077b6]">{selectedCase.case_number}</span>
                  <h2 className="text-lg font-black text-[#002147]">{selectedCase.title}</h2>
                  <p className="text-xs text-slate-600 mt-0.5 font-medium">{selectedCase.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-lg bg-emerald-50 px-3 py-1 text-xs font-black text-emerald-800 border border-emerald-200">
                    STATUS: {selectedCase.status}
                  </span>
                </div>
              </div>

              {/* Evidence Gallery */}
              <div className="space-y-2">
                <h3 className="text-xs font-extrabold text-[#002147] uppercase tracking-wider flex items-center gap-1.5">
                  <ImageIcon className="h-4 w-4 text-[#0077b6]" />
                  <span>Captured Evidence Snapshots</span>
                </h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="relative overflow-hidden rounded-xl border border-slate-300 bg-slate-100">
                    <img
                      src="https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80"
                      alt="CCTV Evidence"
                      className="w-full h-40 object-cover"
                    />
                    <div className="absolute bottom-2 left-2 rounded bg-[#002147] px-2 py-0.5 text-[10px] font-mono font-bold text-white shadow">
                      CAM-GJ01-001 | 2026-09-04 12:45:00
                    </div>
                  </div>
                </div>
              </div>

              {/* Case Notes & Activity */}
              <div className="space-y-3 pt-4 border-t border-slate-200">
                <h3 className="text-xs font-extrabold text-[#002147] uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-[#0077b6]" />
                  <span>Investigator Notes & Log</span>
                </h3>

                <div className="space-y-2.5 max-h-[300px] overflow-y-auto">
                  {(selectedCase.notes || []).map((note) => (
                    <div key={note.id} className="rounded-xl border border-slate-200 bg-[#f8fafc] p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-extrabold text-[#0077b6]">{note.author}</span>
                        <span className="text-slate-500 font-medium">{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-slate-800 font-medium leading-relaxed">{note.note}</p>
                    </div>
                  ))}
                </div>

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} className="flex gap-2 pt-2">
                  <input
                    type="text"
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Add investigator note to case file..."
                    className="flex-1 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
                  />
                  <button
                    type="submit"
                    className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white transition-colors shadow-xs"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>Post Note</span>
                  </button>
                </form>
              </div>
            </div>
          </main>
        ) : (
          <div className="flex min-h-[400px] items-center justify-center text-xs text-slate-500 font-medium">
            Select a case file from the sidebar
          </div>
        )}
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 text-slate-800">
          <div className="w-full max-w-lg rounded-2xl border border-[#cbd5e1] bg-white p-6 space-y-4 shadow-2xl">
            <h2 className="text-lg font-extrabold text-[#002147]">Create New Investigation Case File</h2>
            <form onSubmit={handleCreateCase} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-600 font-extrabold mb-1">Case Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  placeholder="e.g. Stolen Vehicle Track Investigation - SG Highway"
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-600 font-extrabold mb-1">Case Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={3}
                  placeholder="Detailed narrative and initial context..."
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-[#0077b6] hover:bg-[#005b8e] px-4 py-2 text-xs font-extrabold text-white shadow-xs"
                >
                  Initialize Case File
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
