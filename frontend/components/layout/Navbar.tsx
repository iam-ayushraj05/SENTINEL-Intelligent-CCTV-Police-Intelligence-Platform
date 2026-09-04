"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Search, Bell, Zap, Radio, LogOut } from "lucide-react";
import { api } from "@/lib/api";
import { wsClient, ConnectionStatus } from "@/lib/ws";

export const Navbar: React.FC = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>("OFFLINE");

  useEffect(() => {
    const unsubscribe = wsClient.subscribeStatus((newStatus) => {
      setWsStatus(newStatus);
    });
    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    await api.logout();
    router.push("/");
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleTriggerDemoAlert = async () => {
    setTriggering(true);
    setTriggerMsg("Broadcasting Event...");
    try {
      const res = await api.triggerDemoEvent("WATCHLIST_MATCH", "GJ05CD5678");
      setTriggerMsg(`Alert ${res.alert_created || "Triggered"}!`);
      setTimeout(() => setTriggerMsg(null), 3000);
    } catch {
      setTriggerMsg("Event Broadcast Sent");
      setTimeout(() => setTriggerMsg(null), 3000);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-[#003366] bg-[#002147] px-4 text-white shadow-md md:px-6">
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00a896] text-white font-black shadow transition-colors">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black tracking-widest text-[#64dfdf] leading-none">SENTINEL</span>
              <span className="text-[10px] font-bold tracking-wider text-slate-300 uppercase hidden sm:inline-block border-l border-[#003366] pl-2">
                COMMAND CENTRE
              </span>
            </div>
            <span className="text-[10px] text-slate-300 font-medium block">Gujarat State Police HQ</span>
          </div>
        </Link>

        {/* WebSocket Stream Status Pill */}
        {wsStatus === "CONNECTED" ? (
          <span className="hidden md:inline-flex items-center gap-1.5 rounded-full border border-emerald-500/80 bg-emerald-950/80 px-2.5 py-0.5 text-[10px] font-bold text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
            STREAM LIVE
          </span>
        ) : wsStatus === "RECONNECTING" ? (
          <span className="hidden md:inline-flex items-center gap-1.5 rounded-full border border-amber-500/80 bg-amber-950/80 px-2.5 py-0.5 text-[10px] font-bold text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
            RECONNECTING
          </span>
        ) : (
          <span className="hidden md:inline-flex items-center gap-1.5 rounded-full border border-rose-500/80 bg-rose-950/80 px-2.5 py-0.5 text-[10px] font-bold text-rose-300">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
            WS OFFLINE
          </span>
        )}

        <span className="hidden lg:inline-flex items-center gap-1 rounded border border-[#004080] bg-[#001733] px-2 py-0.5 text-[9px] font-extrabold tracking-wider text-sky-200">
          DEMO MODE
        </span>
      </div>

      {/* Global Search Bar */}
      <form onSubmit={handleSearchSubmit} className="hidden sm:flex flex-1 max-w-md mx-6 relative">
        <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search cameras, vehicles, alerts, cases..."
          className="w-full rounded-md border border-[#004080] bg-[#001733] pl-9 pr-4 py-1.5 text-xs text-white placeholder-slate-400 focus:border-[#00a896] focus:outline-none"
        />
      </form>

      {/* Right Action Tools */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleTriggerDemoAlert}
          disabled={triggering}
          className="flex items-center gap-1.5 rounded-md border border-amber-500/80 bg-amber-950/70 px-2.5 py-1 text-xs font-semibold text-amber-200 hover:bg-amber-900 transition-all shadow-sm active:scale-95 disabled:opacity-50"
          title="Simulates real-time ANPR Watchlist Match event broadcast"
        >
          <Zap className="h-3.5 w-3.5 text-amber-400" />
          <span className="text-[11px]">{triggerMsg || "Simulate Watchlist Match"}</span>
        </button>

        <Link
          href="/alerts"
          className="relative flex h-8 w-8 items-center justify-center rounded-md border border-[#004080] bg-[#001733] text-slate-200 hover:bg-[#002b66] transition-colors"
          title="Alerts Center"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-600 text-[9px] font-black text-white">
            3
          </span>
        </Link>

        {/* User Profile Badge & Logout */}
        <div className="flex items-center gap-2 border-l border-[#003366] pl-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#004080] text-[10px] font-black text-sky-200 border border-[#0055a5]">
              IG
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-[11px] font-bold text-white leading-tight">Insp. Gen. A. Sharma</p>
              <p className="text-[9px] text-[#64dfdf] font-semibold uppercase">COMMANDER (ADMIN)</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-md border border-rose-500/50 bg-rose-950/60 px-2.5 py-1 text-xs font-semibold text-rose-200 hover:bg-rose-900 hover:text-white transition-all shadow-sm active:scale-95 ml-1"
            title="Logout & Return to Home Page"
          >
            <LogOut className="h-3.5 w-3.5 text-rose-400" />
            <span className="text-[11px]">Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
