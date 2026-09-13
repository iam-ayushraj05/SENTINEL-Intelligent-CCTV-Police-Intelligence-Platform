"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, Image as ImageIcon, Send, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import type { Investigation } from "@/lib/types";

export default function InvestigationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [caseFile, setCaseFile] = useState<Investigation | null>(null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = params?.id as string;
    if (!id) return;
    api.getInvestigation(id).then(setCaseFile).finally(() => setLoading(false));
  }, [params]);

  const addNote = async (event: FormEvent) => {
    event.preventDefault();
    if (!caseFile || !note.trim()) return;
    const created = await api.addInvestigationNote(caseFile.id, note, "Sub-Inspector Rajesh Patel");
    setCaseFile({ ...caseFile, notes: [...(caseFile.notes || []), created] });
    setNote("");
  };

  if (loading) return <div className="p-8 text-sm text-slate-500">Loading case file...</div>;
  if (!caseFile) return <div className="p-8 text-sm text-rose-700">Case file could not be loaded.</div>;

  return (
    <div className="space-y-6 text-slate-800">
      <button type="button" onClick={() => router.push("/investigations")} className="flex items-center gap-2 text-xs font-bold text-[#0077b6]"><ArrowLeft className="h-4 w-4" /> Back to investigations</button>
      <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4">
          <div><span className="font-mono text-xs font-black text-[#0077b6]">{caseFile.case_number}</span><h1 className="mt-2 text-xl font-black text-[#002147]">{caseFile.title}</h1><p className="mt-1 text-xs text-slate-600">{caseFile.description || "Manual person intelligence case file."}</p></div>
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-black text-emerald-800">STATUS: {caseFile.status}</span>
        </div>

        {caseFile.person_details?.map((person) => (
          <section key={person.id} className="grid gap-4 border-b border-slate-200 py-5 sm:grid-cols-[120px_1fr]">
            <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-xl border border-slate-300 bg-slate-100">
              {person.metadata_json?.photo_url ? <img src={person.metadata_json.photo_url} alt={person.full_name || person.person_code} className="h-full w-full object-cover" /> : <span className="text-center text-[10px] font-bold text-slate-400">NO PHOTO</span>}
            </div>
            <div className="grid gap-x-5 gap-y-2 text-xs sm:grid-cols-2">
              <div><span className="text-slate-500">Person record</span><p className="font-mono font-black text-[#0077b6]">{person.person_code}</p></div>
              <div><span className="text-slate-500">Full name / alias</span><p className="font-bold text-[#002147]">{person.full_name || "Not provided"}{person.alias ? ` (${person.alias})` : ""}</p></div>
              <div><span className="text-slate-500">Date of birth / gender</span><p className="font-bold">{person.date_of_birth || "Not provided"} / {person.gender || "Not provided"}</p></div>
              <div><span className="text-slate-500">Phone / agency</span><p className="font-bold">{person.phone_number || "Not provided"} / {person.agency_unit || "Not provided"}</p></div>
              <div className="sm:col-span-2"><span className="text-slate-500">Address</span><p className="font-medium">{person.address || "Not provided"}</p></div>
              <div className="sm:col-span-2"><span className="text-slate-500">Record notes</span><p className="font-medium">{person.notes || "No additional notes"}</p></div>
            </div>
          </section>
        ))}

        <section className="space-y-3 border-b border-slate-200 py-5">
          <h2 className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-[#002147]"><ImageIcon className="h-4 w-4 text-[#0077b6]" /> Captured evidence and identity files</h2>
          {caseFile.evidence?.length ? <div className="grid gap-3 sm:grid-cols-2">{caseFile.evidence.map((item) => <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs font-bold text-[#0077b6]">{item.code}<span className="mt-1 block text-[11px] text-slate-500">{item.type}</span></a>)}</div> : <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-xs text-slate-500">No files attached yet. Uploaded identity files will appear here as case evidence.</div>}
        </section>

        <section className="space-y-3 pt-5">
          <h2 className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-[#002147]"><FileText className="h-4 w-4 text-[#0077b6]" /> Investigator notes and log</h2>
          <div className="space-y-2">{(caseFile.notes || []).map((item) => <div key={item.id} className="rounded-xl border border-slate-200 bg-[#f8fafc] p-3"><div className="flex justify-between text-[10px]"><span className="font-black text-[#0077b6]">{item.author}</span><span className="text-slate-500">{new Date(item.created_at).toLocaleString()}</span></div><p className="mt-1 text-xs leading-relaxed text-slate-800">{item.note}</p></div>)}</div>
          <form onSubmit={addNote} className="flex gap-2 pt-2"><input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add investigator note to case file..." className="flex-1 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs outline-none focus:border-[#0077b6]" /><button type="submit" className="flex items-center gap-1.5 rounded-lg bg-[#0077b6] px-4 py-2 text-xs font-black text-white"><Send className="h-3.5 w-3.5" /> Post Note</button></form>
        </section>
        <div className="mt-5 flex items-center gap-2 border-t border-slate-200 pt-4 text-[11px] text-slate-500"><ShieldCheck className="h-4 w-4 text-emerald-600" /> Structured case record with audit-backed notes and protected evidence references.</div>
      </div>
    </div>
  );
}
