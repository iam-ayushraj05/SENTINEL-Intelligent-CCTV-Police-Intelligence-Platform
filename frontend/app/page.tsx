"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  Lock,
  User as UserIcon,
  Phone,
  Video,
  Radio,
  CheckCircle2,
  Car,
  FileText,
  AlertTriangle,
  ArrowRight,
  Globe,
  Cpu,
  Eye,
  Server,
  Layers,
  ChevronLeft,
  ChevronRight,
  X,
  Building2,
  Briefcase,
  MapPin,
} from "lucide-react";
import { api } from "@/lib/api";

const DISTRICT_SERVERS = [
  { id: "ahmedabad", name: "Ahmedabad City Command", code: "GJ01", online: true },
  { id: "gandhinagar", name: "Gandhinagar State Capital Range", code: "GJ18", online: true },
  { id: "surat", name: "Surat City Command", code: "GJ05", online: true },
  { id: "vadodara", name: "Vadodara City Command", code: "GJ06", online: true },
  { id: "rajkot", name: "Rajkot City Command", code: "GJ03", online: true },
  { id: "bhavnagar", name: "Bhavnagar Range", code: "GJ04", online: true },
  { id: "jamnagar", name: "Jamnagar Command", code: "GJ10", online: true },
  { id: "central", name: "Central Umbrella Dashboard (State HQ)", code: "GJ99", online: true },
  { id: "nmc", name: "NMC / Mobile Dispatch", code: "GJ00", online: true },
];

const CAROUSEL_SLIDES = [
  {
    title: "SENTINEL (ABHAY GUJARAT)",
    subtitle: "Unified AI Video Surveillance & Intelligent Policing Platform",
    tagline: "Improvement of Public Safety • Reduction in Crime • Evidence Capture",
  },
  {
    title: "INTEGRATED ANPR & TRAFFIC",
    subtitle: "Automated License Plate Recognition & Speed Corridor Monitoring",
    tagline: "Real-time Watchlist Matching Across 120+ Gujarat Checkposts",
  },
  {
    title: "CAD & DIAL 100/112 DISPATCH",
    subtitle: "Computer Aided Dispatch & Immediate PCR Patrol Deployment",
    tagline: "Instant Caller Geolocation & GIS Map Mapping",
  },
];

export default function AbhayGujaratLightPortalPage() {
  const router = useRouter();
  const [activeSlide, setActiveSlide] = useState(0);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [selectedServer, setSelectedServer] = useState("ahmedabad");
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      router.push("/dashboard");
    } catch {
      // Demo fallback redirect
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const nextSlide = () => {
    setActiveSlide((prev) => (prev + 1) % CAROUSEL_SLIDES.length);
  };

  const prevSlide = () => {
    setActiveSlide((prev) => (prev - 1 + CAROUSEL_SLIDES.length) % CAROUSEL_SLIDES.length);
  };

  return (
    <div className="min-h-screen bg-[#eef6fb] text-slate-800 flex flex-col font-sans">
      {/* 1. ABHAY OFFICIAL GOVERNMENT TOP HEADER BANNER */}
      <header className="bg-[#002147] text-white border-b-4 border-[#00a896] px-4 md:px-8 py-3.5 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Logo & Emblem */}
          <div className="flex items-center gap-3.5">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#00a896] text-white font-black shadow-md">
              <Shield className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-black tracking-widest text-[#64dfdf] uppercase">GOVERNMENT OF GUJARAT</span>
                <span className="text-[9px] font-bold bg-[#003366] text-sky-200 px-2 py-0.5 rounded border border-[#004080]">
                  HOME DEPARTMENT
                </span>
              </div>
              <h1 className="text-2xl font-black text-white tracking-tight">SENTINEL</h1>
              <p className="text-[11px] text-slate-300">Unified CCTV Intelligence & Smart Policing Command Centre</p>
            </div>
          </div>

          {/* Right Header Actions: Department Login Button & Ministers Seals */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowLoginModal(true)}
              className="rounded-lg bg-[#00a896] hover:bg-[#028090] text-white font-extrabold px-5 py-2.5 text-xs shadow-md transition-all flex items-center gap-2"
            >
              <Lock className="h-4 w-4" />
              <span>Department Login</span>
            </button>

            {/* Official Leadership Badges */}
            <div className="hidden sm:flex items-center gap-3 border-l border-[#003366] pl-4 text-[11px]">
              <div className="flex items-center gap-2 bg-[#001733] border border-[#003366] rounded-lg px-2.5 py-1.5">
                <div className="h-7 w-7 rounded-full bg-[#004080] flex items-center justify-center font-bold text-sky-300 shrink-0">
                  BP
                </div>
                <div>
                  <strong className="block text-white font-bold leading-tight">Sh. Bhupendrabhai Patel</strong>
                  <span className="text-[10px] text-slate-300">Hon'ble Chief Minister</span>
                </div>
              </div>

              <div className="flex items-center gap-2 bg-[#001733] border border-[#003366] rounded-lg px-2.5 py-1.5">
                <div className="h-7 w-7 rounded-full bg-[#004080] flex items-center justify-center font-bold text-amber-300 shrink-0">
                  HS
                </div>
                <div>
                  <strong className="block text-white font-bold leading-tight">Sh. Harsh Sanghavi</strong>
                  <span className="text-[10px] text-slate-300">Hon'ble Minister of State Home</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 2. HERO MAIN SECTION (Split: Left Carousel Graphic + Right Server Command List) */}
      <section className="max-w-7xl w-full mx-auto px-4 md:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
          {/* Left: ABHAY Circular Carousel Hub */}
          <div className="relative overflow-hidden rounded-2xl border border-[#bde0fe] bg-gradient-to-br from-[#002b66] via-[#002147] to-[#001529] p-8 md:p-12 flex flex-col justify-between min-h-[380px] shadow-lg text-white">
            {/* Nav Arrows */}
            <button
              onClick={prevSlide}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white hover:bg-[#00a896] transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={nextSlide}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white hover:bg-[#00a896] transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>

            {/* Circular Hub Diagram */}
            <div className="flex flex-col items-center justify-center text-center my-auto space-y-4">
              <div className="relative flex items-center justify-center">
                {/* Outer Ring Nodes */}
                <div className="h-44 w-44 md:h-56 md:w-56 rounded-full border-2 border-dashed border-sky-300/50 flex items-center justify-center">
                  <span className="absolute -top-3 text-[10px] font-black bg-[#00a896] text-white px-2.5 py-0.5 rounded shadow">
                    Public Safety
                  </span>
                  <span className="absolute -bottom-3 text-[10px] font-black bg-[#0284c7] text-white px-2.5 py-0.5 rounded shadow">
                    Crime Reduction
                  </span>
                  <span className="absolute -left-4 text-[10px] font-black bg-[#d97706] text-white px-2.5 py-0.5 rounded shadow">
                    Emergency Assist
                  </span>
                  <span className="absolute -right-4 text-[10px] font-black bg-[#7c3aed] text-white px-2.5 py-0.5 rounded shadow">
                    Evidence Capture
                  </span>
                </div>

                {/* Inner Center Emblem */}
                <div className="absolute flex flex-col items-center justify-center h-28 w-28 md:h-36 md:w-36 rounded-full bg-white text-[#002147] font-black shadow-xl border-4 border-[#00a896]">
                  <Shield className="h-10 w-10 text-[#002147]" />
                  <span className="text-sm font-black tracking-widest mt-1">SENTINEL</span>
                </div>
              </div>

              {/* Text Info */}
              <div className="max-w-xl space-y-1.5">
                <div className="mb-2 inline-flex items-center rounded-full border border-[#00a896] bg-[#0b5f76]/40 px-3 py-1 text-[10px] font-black uppercase tracking-[0.22em] text-[#d9f9f4]">
                  SYNTHETIC DEMO DATA
                </div>
                <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">
                  SENTINEL
                </h2>
                <p className="text-xs font-bold text-sky-200 uppercase tracking-wider">
                  Unified CCTV Intelligence & Smart Policing Platform
                </p>
                <p className="text-xs text-slate-300 font-medium">
                  From Fragmented Cameras to Unified Intelligence.
                </p>
              </div>
            </div>

            {/* Dots Pagination */}
            <div className="flex justify-center gap-2 pt-4">
              {CAROUSEL_SLIDES.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveSlide(idx)}
                  className={`h-2.5 rounded-full transition-all ${
                    activeSlide === idx ? "w-8 bg-[#00a896]" : "w-2.5 bg-white/40"
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Right: Web Servers / Command List (White Card Container) */}
          <div className="rounded-2xl border border-[#cbd5e1] bg-white p-5 flex flex-col justify-between shadow-md">
            <div>
              <div className="flex items-center justify-between border-b border-slate-200 pb-2.5 mb-3">
                <h3 className="font-extrabold text-[#002147] text-xs uppercase tracking-wider flex items-center gap-2">
                  <Server className="h-4 w-4 text-[#0077b6]" />
                  <span>District Command Web Servers</span>
                </h3>
                <span className="h-2 w-2 rounded-full bg-[#10b981]" />
              </div>

              <div className="space-y-1.5 max-h-[310px] overflow-y-auto pr-1">
                {DISTRICT_SERVERS.map((server) => (
                  <button
                    key={server.id}
                    onClick={() => {
                      setSelectedServer(server.id);
                      setShowLoginModal(true);
                    }}
                    className="w-full flex items-center justify-between rounded-lg border border-slate-200 bg-[#f8fafc] px-3 py-2 text-xs font-bold text-slate-700 hover:border-[#0077b6] hover:bg-[#e2f1f8] transition-all group text-left"
                  >
                    <div className="flex items-center gap-2">
                      <Layers className="h-3.5 w-3.5 text-[#0077b6]" />
                      <span>{server.name}</span>
                    </div>
                    <span className="font-mono text-[10px] text-[#0077b6] font-bold bg-[#e2f1f8] px-2 py-0.5 rounded border border-[#bde0fe]">
                      CONNECT
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200">
              <button
                onClick={() => setShowLoginModal(true)}
                className="w-full rounded-lg bg-[#0077b6] hover:bg-[#005b8e] text-white font-extrabold py-2.5 text-xs shadow transition-all uppercase tracking-wider"
              >
                Access Command Dashboard →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 3. SECONDARY FEATURE CARDS GRID (3 Columns) */}
      <section className="max-w-7xl w-full mx-auto px-4 md:px-8 py-2">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* CARD 1: DIAL 100/112 */}
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 flex items-center justify-between shadow-sm">
            <div className="space-y-1">
              <span className="text-[10px] font-black text-amber-800 uppercase tracking-widest block">EMERGENCY DISPATCH</span>
              <h3 className="text-xl font-black text-amber-950">Dial 100 / 112</h3>
              <p className="text-xs text-amber-800">Computer Aided Dispatch & Patrol Deployment</p>
            </div>
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-amber-500 text-white font-black shadow">
              <Phone className="h-7 w-7" />
            </div>
          </div>

          {/* CARD 2: ITMS & ANPR */}
          <div className="rounded-2xl border border-sky-200 bg-sky-50 p-6 flex items-center justify-between shadow-sm">
            <div className="space-y-1">
              <span className="text-[10px] font-black text-sky-800 uppercase tracking-widest block">TRAFFIC MANAGEMENT</span>
              <h3 className="text-xl font-black text-sky-950">Integrated ITMS & ANPR</h3>
              <p className="text-xs text-sky-800">Automated Vehicle & Speed Tracking</p>
            </div>
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#0284c7] text-white font-black shadow">
              <Car className="h-7 w-7" />
            </div>
          </div>

          {/* CARD 3: FACE RECOGNITION & AI ANALYTICS */}
          <div className="rounded-2xl border border-purple-200 bg-purple-50 p-6 flex items-center justify-between shadow-sm">
            <div className="space-y-1">
              <span className="text-[10px] font-black text-purple-800 uppercase tracking-widest block">AI ANALYTICS</span>
              <h3 className="text-xl font-black text-purple-950">Face & Video AI System</h3>
              <p className="text-xs text-purple-800">Real-time Object & Crowding Detection</p>
            </div>
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#7c3aed] text-white font-black shadow">
              <Cpu className="h-7 w-7" />
            </div>
          </div>
        </div>
      </section>

      {/* 4. DETAILED FEATURE SHOWCASE SECTIONS (Clean White Cards as seen in Screenshots) */}
      <section className="max-w-7xl w-full mx-auto px-4 md:px-8 py-6 space-y-8">
        {/* SECTION 1: Video Surveillance System */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-center shadow-sm">
          <div className="flex flex-col items-center justify-center bg-[#e2f1f8] border border-[#bde0fe] rounded-xl p-6 min-h-[220px]">
            <Video className="h-20 w-20 text-[#0077b6]" />
            <span className="mt-3 font-mono text-xs text-[#002147] font-bold bg-white px-3 py-1 rounded border border-[#bde0fe] shadow-sm">
              2,500+ 4K CCTV CAMERAS ATTACHED
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-[#00a896]" />
              <h3 className="text-xl font-extrabold text-[#002147]">24x7 Video Surveillance Network</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Continuous 24x7 live monitoring with 4K CCTV cameras across Gujarat.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Over 2,500 cameras across key junction locations, highways & public zones.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Real-time crime scene observation, crowd management & incident verification.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Video analytics for rapid incident detection & suspect tracking.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* SECTION 2: CAD & Dial 100 / 112 Emergency Dispatch */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-center shadow-sm">
          <div className="space-y-3 order-2 md:order-1">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-amber-500" />
              <h3 className="text-xl font-extrabold text-[#002147]">CAD & Dial 100 / 112 (Computer Aided Dispatch)</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Computer-aided dispatch for emergency distress calls.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Integrated with Dial 100, Emergency 112, and Women Helpline 181.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Automatic caller location lookup and details plotted live on GIS map.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Rapid response deployment to nearest police patrol vehicle.</span>
              </li>
            </ul>
          </div>
          <div className="flex flex-col items-center justify-center bg-amber-50 border border-amber-200 rounded-xl p-6 min-h-[220px] order-1 md:order-2">
            <Radio className="h-20 w-20 text-amber-600" />
            <span className="mt-3 font-mono text-xs text-amber-900 font-bold bg-white px-3 py-1 rounded border border-amber-300 shadow-sm">
              24x7 CAD CALL DISPATCH ACTIVE
            </span>
          </div>
        </div>

        {/* SECTION 3: Intelligent Traffic Management System (ITMS) */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-center shadow-sm">
          <div className="flex flex-col items-center justify-center bg-emerald-50 border border-emerald-200 rounded-xl p-6 min-h-[220px]">
            <Car className="h-20 w-20 text-emerald-600" />
            <span className="mt-3 font-mono text-xs text-emerald-900 font-bold bg-white px-3 py-1 rounded border border-emerald-300 shadow-sm">
              120+ AUTOMATED ANPR CHECKPOSTS
            </span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-emerald-500" />
              <h3 className="text-xl font-extrabold text-[#002147]">Intelligent Traffic Management System (ITMS)</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>AI-based traffic monitoring and signal automation.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Automatic vehicle counting and violation detection.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Integration with e-Challan and ANPR license plate databases.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Real-time congestion and incident alerts.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* SECTION 4: Geographical Information System (GIS) */}
        <div className="rounded-2xl border border-[#cbd5e1] bg-white p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-8 items-center shadow-sm">
          <div className="space-y-3 order-2 md:order-1">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-sky-500" />
              <h3 className="text-xl font-extrabold text-[#002147]">Geographical Information System (GIS)</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Crime hotspot mapping and predictive spatial analysis.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Resource optimization and quick patrol deployment.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Integration with city GIS maps and emergency services.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-[#00a896] shrink-0 mt-0.5" />
                <span>Supports incident response and strategic police planning.</span>
              </li>
            </ul>
          </div>
          <div className="flex flex-col items-center justify-center bg-[#e2f1f8] border border-[#bde0fe] rounded-xl p-6 min-h-[220px] order-1 md:order-2">
            <MapPin className="h-20 w-20 text-[#0077b6]" />
            <span className="mt-3 font-mono text-xs text-[#002147] font-bold bg-white px-3 py-1 rounded border border-[#bde0fe] shadow-sm">
              STATE GIS HOTSPOT MAPPING
            </span>
          </div>
        </div>
      </section>

      {/* 5. DEPARTMENT LOGIN MODAL */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md rounded-2xl border border-[#cbd5e1] bg-white p-6 space-y-5 shadow-2xl relative text-slate-800">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 p-1 rounded-lg border border-slate-200 bg-slate-100"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-[#0077b6]" />
                <h3 className="font-extrabold text-[#002147] text-base">DEPARTMENT LOGIN GATEWAY</h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Enter officer badge credentials to access the internal command dashboard.
              </p>
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg border border-rose-300 bg-rose-50 p-3 text-xs text-rose-700">
                <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-extrabold uppercase text-slate-600 mb-1">Select Command District</label>
                <select
                  value={selectedServer}
                  onChange={(e) => setSelectedServer(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2.5 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                >
                  {DISTRICT_SERVERS.map((s) => (
                    <option key={s.id} value={s.id}>
                      [{s.code}] {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-extrabold uppercase text-slate-600 mb-1">Officer Badge ID / Username</label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    placeholder="e.g. admin"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-extrabold uppercase text-slate-600 mb-1">Secure Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full rounded-lg border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-800 focus:border-[#0077b6] focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-[#00a896] hover:bg-[#028090] text-white py-3 text-xs font-black uppercase shadow transition-all active:scale-[0.99] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <span>{loading ? "AUTHENTICATING..." : "AUTHORIZE & ENTER COMMAND CENTER"}</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>

            <div className="border-t border-slate-200 pt-4 space-y-2">
              <p className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider text-center">
                QUICK DEMO ACCESS
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => { setUsername("admin"); setPassword("admin123"); router.push("/dashboard"); }}
                  className="flex-1 rounded border border-slate-300 bg-slate-100 py-2 text-[10px] font-extrabold text-[#0077b6] hover:bg-slate-200"
                >
                  Inspector General
                </button>
                <button
                  onClick={() => { setUsername("operator01"); setPassword("operator123"); router.push("/dashboard"); }}
                  className="flex-1 rounded border border-slate-300 bg-slate-100 py-2 text-[10px] font-extrabold text-slate-700 hover:bg-slate-200"
                >
                  Duty Operator
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. OFFICIAL GOVERNMENT FOOTER (Deep Navy Background matching Screenshots) */}
      <footer className="bg-[#002147] text-white border-t-4 border-[#00a896] px-6 py-8 text-center text-xs space-y-3 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-slate-300">
          <div className="text-left space-y-1">
            <strong className="block text-white font-extrabold text-sm">
              GUJARAT STATE POLICE COMMAND & CONTROL CENTRE (SENTINEL / ABHAY GUJARAT)
            </strong>
            <p className="text-[11px]">Home Department, Government of Gujarat • State Police HQ, Gandhinagar</p>
          </div>
          <div className="text-right space-y-1 text-[11px]">
            <p><strong>Nodal Officer Helpline:</strong> 079-23250000 | <strong>Contact Us:</strong> 079-112</p>
            <p className="text-slate-400">Website Visitor Count: 0008492 | Last Updated: 2026-09-04</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
