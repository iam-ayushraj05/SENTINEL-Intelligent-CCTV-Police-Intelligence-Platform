"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { FileArchive, FileImage, FileText, FolderOpen, LockKeyhole, Search, Trash2, UploadCloud, ShieldCheck, ClipboardList } from "lucide-react";
import { fetchAPI } from "@/lib/api";

type DocumentItem = {
  id: string;
  title: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  category: string | null;
  tags: string[];
  uploaded_at: string;
  is_sensitive: boolean;
};

type EvidenceItem = {
  id: string;
  evidence_id: string;
  filename: string;
  mime_type: string;
  sha256: string;
  evidence_type: string;
  description?: string;
  status: string;
  current_location?: string;
  current_custodian?: string;
  created_at: string;
};

const FALLBACK_DOCUMENTS: DocumentItem[] = [
  { id: "demo-1", title: "Aadhaar identity record", filename: "identity-card.pdf", mime_type: "application/pdf", size_bytes: 248000, category: "Identity", tags: ["government", "id"], uploaded_at: "2026-09-05T10:20:00Z", is_sensitive: true },
  { id: "demo-2", title: "Annual insurance policy", filename: "insurance-2026.pdf", mime_type: "application/pdf", size_bytes: 810000, category: "Finance", tags: ["policy", "renewal"], uploaded_at: "2026-09-02T08:10:00Z", is_sensitive: true },
  { id: "demo-3", title: "Medical report scan", filename: "health-report.png", mime_type: "image/png", size_bytes: 1250000, category: "Medical", tags: ["health"], uploaded_at: "2026-08-28T16:44:00Z", is_sensitive: true },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function formatBytes(bytes: number) {
  return `${(bytes / (1024 * 1024)).toFixed(bytes > 1024 * 1024 ? 1 : 2)} MB`;
}

function FileIcon({ mime }: { mime: string }) {
  if (mime.startsWith("image/")) return <FileImage className="h-5 w-5 text-emerald-600" />;
  if (mime === "text/csv" || mime === "application/csv") return <FileArchive className="h-5 w-5 text-amber-600" />;
  return <FileText className="h-5 w-5 text-[#0077b6]" />;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All categories");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("Identity");
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);
  const [evidenceType, setEvidenceType] = useState("DIGITAL");
  const [evidenceDescription, setEvidenceDescription] = useState("");
  const [evidenceBusy, setEvidenceBusy] = useState(false);
  const [evidenceMessage, setEvidenceMessage] = useState("");

  const loadDocuments = async () => {
    try {
      const params = new URLSearchParams();
      if (query) params.set("q", query);
      if (category !== "All categories") params.set("category", category);
      setDocuments(await fetchAPI<DocumentItem[]>(`/documents?${params.toString()}`));
    } catch {
      const normalized = query.toLowerCase();
      setDocuments(FALLBACK_DOCUMENTS.filter((item) => !normalized || `${item.title} ${item.filename} ${item.tags.join(" ")}`.toLowerCase().includes(normalized)));
    }
  };

  useEffect(() => { loadDocuments(); }, [query, category]);

  useEffect(() => {
    fetchAPI<EvidenceItem[]>("/evidence").then(setEvidence).catch(() => setEvidence([]));
  }, []);

  const handleUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedFile) return;
    setBusy(true);
    setMessage("");
    const body = new FormData();
    body.append("file", selectedFile);
    body.append("title", title);
    body.append("category", uploadCategory);
    body.append("tags", tags);
    try {
      const response = await fetch(`${API_BASE}/documents`, { method: "POST", body });
      if (!response.ok) throw new Error("Upload failed");
      setMessage("Document encrypted and stored");
      setSelectedFile(null); setTitle(""); setTags("");
      await loadDocuments();
    } catch {
      setMessage("Backend unavailable. Start the API before uploading.");
    } finally { setBusy(false); }
  };

  const deleteDocument = async (id: string) => {
    if (id.startsWith("demo-")) return;
    await fetch(`${API_BASE}/documents/${id}`, { method: "DELETE" });
    await loadDocuments();
  };

  const handleEvidenceUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!evidenceFile) return;
    setEvidenceBusy(true);
    setEvidenceMessage("");
    const body = new FormData();
    body.append("file", evidenceFile);
    body.append("evidence_type", evidenceType);
    body.append("description", evidenceDescription);
    try {
      const response = await fetch(`${API_BASE}/evidence`, { method: "POST", body });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Evidence intake failed");
      setEvidence([payload, ...evidence]);
      setEvidenceFile(null); setEvidenceDescription("");
      setEvidenceMessage(`Preserved as ${payload.evidence_id}; SHA-256 recorded.`);
    } catch (error) {
      setEvidenceMessage(error instanceof Error ? error.message : "Evidence intake failed");
    } finally { setEvidenceBusy(false); }
  };

  const categories = ["All categories", ...Array.from(new Set(documents.map((item) => item.category).filter(Boolean) as string[]))];

  return (
    <div className="space-y-6 text-slate-800">
      <header className="flex flex-col gap-3 border-b border-slate-300 pb-5 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.24em] text-[#0077b6]">Private records vault</p>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-[#002147]">DOCUMENT CENTRE</h1>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-[11px] font-extrabold text-emerald-800"><LockKeyhole className="h-4 w-4" /> AES-256 STORAGE</div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <section className="min-w-0 space-y-4">
          <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row">
            <label className="relative flex-1"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title, filename, OCR text, or tag" className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-[#0077b6]" /></label>
            <select value={category} onChange={(event) => setCategory(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 outline-none focus:border-[#0077b6]">{categories.map((item) => <option key={item}>{item}</option>)}</select>
          </div>
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3"><h2 className="flex items-center gap-2 text-sm font-black text-[#002147]"><FolderOpen className="h-4 w-4 text-[#0077b6]" /> RECENT UPLOADS</h2><span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{documents.length} records</span></div>
            <div className="divide-y divide-slate-100">{documents.map((item) => <article key={item.id} className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50"><div className="rounded-lg bg-slate-100 p-2"><FileIcon mime={item.mime_type} /></div><div className="min-w-0 flex-1"><h3 className="truncate text-sm font-bold text-slate-800">{item.title}</h3><p className="truncate text-[11px] text-slate-500">{item.filename} · {formatBytes(item.size_bytes)} · {new Date(item.uploaded_at).toLocaleDateString("en-IN")}</p><div className="mt-1 flex flex-wrap gap-1">{item.category && <span className="rounded bg-[#e2f1f8] px-1.5 py-0.5 text-[10px] font-bold text-[#0077b6]">{item.category}</span>}{item.tags.map((tag) => <span key={tag} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">#{tag}</span>)}</div></div><button onClick={() => deleteDocument(item.id)} title="Delete document" className="rounded-md p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600"><Trash2 className="h-4 w-4" /></button></article>)}{!documents.length && <p className="px-4 py-10 text-center text-sm text-slate-500">No documents match this search.</p>}</div>
          </div>
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-200 px-4 py-3"><h2 className="flex items-center gap-2 text-sm font-black text-[#002147]"><ShieldCheck className="h-4 w-4 text-emerald-600" /> EVIDENCE REGISTER</h2><span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{evidence.length} preserved</span></div><div className="divide-y divide-slate-100">{evidence.map((item) => <article key={item.id} className="px-4 py-3"><div className="flex items-center justify-between gap-3"><div><p className="font-mono text-xs font-black text-[#0077b6]">{item.evidence_id}</p><p className="text-sm font-bold text-slate-800">{item.filename}</p></div><span className="rounded bg-emerald-50 px-2 py-1 text-[10px] font-black text-emerald-700">{item.status}</span></div><p className="mt-1 text-[11px] text-slate-500">{item.evidence_type} · {item.current_location || "Evidence intake"} · {item.current_custodian || "Unassigned"}</p><p className="mt-1 truncate font-mono text-[10px] text-slate-400" title={item.sha256}>SHA-256: {item.sha256}</p></article>)}{!evidence.length && <p className="px-4 py-8 text-center text-xs text-slate-500">No preserved evidence records.</p>}</div></section>
        </section>

        <form onSubmit={handleUpload} className="h-fit rounded-xl border border-[#bde0fe] bg-[#f8fcff] p-5 shadow-sm"><div className="flex items-center gap-2 border-b border-[#d8edf8] pb-3"><UploadCloud className="h-5 w-5 text-[#0077b6]" /><h2 className="text-sm font-black text-[#002147]">ADD DOCUMENT</h2></div><label className="mt-4 block cursor-pointer rounded-lg border-2 border-dashed border-[#8ccfe5] bg-white p-5 text-center hover:bg-[#eef9fd]"><input type="file" accept=".pdf,.jpg,.jpeg,.png,.csv" onChange={(event: ChangeEvent<HTMLInputElement>) => setSelectedFile(event.target.files?.[0] || null)} className="sr-only" /><span className="text-xs font-bold text-[#0077b6]">{selectedFile ? selectedFile.name : "Choose PDF, JPG, PNG, or CSV"}</span><span className="mt-1 block text-[10px] text-slate-500">Maximum 25 MB</span></label><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Document title" className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#0077b6]" /><select value={uploadCategory} onChange={(event) => setUploadCategory(event.target.value)} className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none"><option>Identity</option><option>Finance</option><option>Medical</option><option>Legal</option><option>Biometric Log</option></select><input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Tags separated by commas" className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#0077b6]" /><button disabled={!selectedFile || busy} className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-[#0077b6] px-4 py-2.5 text-xs font-black text-white transition hover:bg-[#005f91] disabled:cursor-not-allowed disabled:opacity-50"><UploadCloud className="h-4 w-4" />{busy ? "ENCRYPTING..." : "UPLOAD SECURELY"}</button>{message && <p className="mt-3 text-center text-[11px] font-bold text-slate-600">{message}</p>}</form>
        <form onSubmit={handleEvidenceUpload} className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50/40 p-5 shadow-sm"><div className="flex items-center gap-2 border-b border-emerald-200 pb-3"><ClipboardList className="h-5 w-5 text-emerald-700" /><h2 className="text-sm font-black text-[#002147]">PRESERVE EVIDENCE</h2></div><label className="mt-4 block cursor-pointer rounded-lg border-2 border-dashed border-emerald-300 bg-white p-4 text-center"><input type="file" accept=".pdf,.jpg,.jpeg,.png,.csv,.mp4,.webm,.wav,.mp3" onChange={(event: ChangeEvent<HTMLInputElement>) => setEvidenceFile(event.target.files?.[0] || null)} className="sr-only" /><span className="text-xs font-bold text-emerald-700">{evidenceFile ? evidenceFile.name : "Choose evidence file"}</span><span className="mt-1 block text-[10px] text-slate-500">Original is encrypted, hashed, and retained separately</span></label><div className="mt-3 grid gap-3 sm:grid-cols-2"><select value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"><option>DIGITAL</option><option>CCTV</option><option>PHOTO</option><option>VIDEO</option><option>AUDIO</option><option>FORENSIC</option><option>PHYSICAL</option></select><input value={evidenceDescription} onChange={(event) => setEvidenceDescription(event.target.value)} placeholder="Evidence description" className="rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div><button disabled={!evidenceFile || evidenceBusy} className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-50"><ShieldCheck className="h-4 w-4" />{evidenceBusy ? "PRESERVING..." : "PRESERVE WITH SHA-256"}</button>{evidenceMessage && <p className="mt-3 text-center text-[11px] font-bold text-slate-700">{evidenceMessage}</p>}</form>
      </div>
    </div>
  );
}