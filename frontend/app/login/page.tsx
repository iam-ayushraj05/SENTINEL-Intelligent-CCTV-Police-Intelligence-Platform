"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Lock, User as UserIcon, AlertCircle, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.login(username, password);
      router.push("/");
    } catch {
      setError("Invalid badge credentials or authorization failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[85vh] items-center justify-center p-4">
      <div className="w-full max-w-4xl overflow-hidden rounded-2xl border border-[#243b53] bg-[#0d1b2a] shadow-2xl grid grid-cols-1 md:grid-cols-2">
        {/* LEFT: Large Dark Visual Area */}
        <div className="relative p-8 md:p-10 bg-gradient-to-br from-[#07111f] via-[#0a1626] to-[#0d1b2a] flex flex-col justify-between border-b md:border-b-0 md:border-r border-[#243b53]">
          <div className="space-y-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-500 text-slate-950 font-black shadow-lg shadow-sky-950/60">
              <Shield className="h-7 w-7" />
            </div>
            <div>
              <span className="text-xs font-black tracking-[0.25em] text-sky-400 uppercase">STATE POLICE COMMAND</span>
              <h1 className="text-3xl font-black text-white tracking-tight mt-1">SENTINEL</h1>
              <p className="text-xs font-extrabold text-sky-300 tracking-wider uppercase mt-1">
                AI-POWERED COMMAND & INTELLIGENCE
              </p>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed pt-2">
              Unified CCTV intelligence for faster, smarter and more informed operations. Integrated ANPR, vehicle trajectory tracking, and automated AI alert correlation engine.
            </p>
          </div>

          <div className="pt-8 border-t border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>Gujarat State Police Control Centre Gateway</span>
            </div>
            <p className="text-[10px] text-slate-500">Restricted Official Personnel Access Only</p>
          </div>
        </div>

        {/* RIGHT: Login Card */}
        <div className="p-8 md:p-10 flex flex-col justify-between bg-[#0a1626]">
          <div>
            <h2 className="text-xl font-black text-white">COMMAND SIGN IN</h2>
            <p className="text-xs text-slate-400 mt-1">Enter your badged credentials to initiate session</p>

            {error && (
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-800 bg-rose-950/80 p-3 text-xs text-rose-300">
                <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-extrabold uppercase text-slate-400 mb-1.5">User Badge / Username</label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full rounded-lg border border-[#243b53] bg-[#07111f] pl-10 pr-4 py-2.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-extrabold uppercase text-slate-400 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full rounded-lg border border-[#243b53] bg-[#07111f] pl-10 pr-4 py-2.5 text-xs text-white focus:border-sky-500 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-sky-500 py-3 text-xs font-black uppercase text-slate-950 shadow-lg shadow-sky-950/50 hover:bg-sky-400 transition-all active:scale-[0.99] disabled:opacity-50 mt-2"
              >
                {loading ? "Authenticating Session..." : "SIGN IN"}
              </button>
            </form>
          </div>

          <div className="mt-6 border-t border-slate-800 pt-4 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500 font-bold uppercase text-[10px]">Secure Operations Environment</span>
              <span className="font-extrabold text-emerald-400 text-[10px] flex items-center gap-1">
                ● SYSTEM STATUS OPERATIONAL
              </span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => { setUsername("admin"); setPassword("admin123"); }}
                className="flex-1 rounded border border-slate-700 bg-[#07111f] py-1.5 text-[10px] font-extrabold text-slate-300 hover:bg-slate-800"
              >
                Command Admin
              </button>
              <button
                onClick={() => { setUsername("operator01"); setPassword("operator123"); }}
                className="flex-1 rounded border border-slate-700 bg-[#07111f] py-1.5 text-[10px] font-extrabold text-slate-300 hover:bg-slate-800"
              >
                Duty Operator
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
