"use client";

import React, { useEffect, useState } from "react";
import { AuditLogItem } from "@/lib/types";
import { api, MOCK_AUDIT_LOGS } from "@/lib/api";
import { FileText, Search, ShieldCheck } from "lucide-react";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getAuditLogs().then((data) => setLogs(data.length ? data : MOCK_AUDIT_LOGS));
  }, []);

  const filtered = logs.filter((l) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        l.username.toLowerCase().includes(q) ||
        l.action.toLowerCase().includes(q) ||
        l.resource.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="border-b border-slate-300 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
            <FileText className="h-6 w-6 text-[#0077b6]" />
            <span>SYSTEM SECURITY & AUDIT TRAIL LOGS</span>
          </h1>
          <p className="mt-1 text-xs text-slate-600 font-medium">Tamper-Evident System Audit Logs of Operator Actions & Database Queries</p>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search action, user, resource..."
            className="w-64 rounded-lg border border-slate-300 bg-slate-50 pl-9 pr-4 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-[#0077b6] focus:outline-none"
          />
        </div>
      </div>

      {/* Audit Table */}
      <div className="rounded-2xl border border-[#cbd5e1] bg-white overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-300 bg-[#f8fafc] text-slate-600 font-extrabold uppercase tracking-wider">
            <tr>
              <th className="p-3.5">Timestamp</th>
              <th className="p-3.5">Operator</th>
              <th className="p-3.5">Action Type</th>
              <th className="p-3.5">Target Resource</th>
              <th className="p-3.5">IP Address</th>
              <th className="p-3.5 text-right">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700 font-mono">
            {filtered.map((log) => (
              <tr key={log.id} className="hover:bg-[#e2f1f8]/40 transition-colors">
                <td className="p-3.5 text-slate-500 font-bold">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="p-3.5 font-black text-[#0077b6]">{log.username}</td>
                <td className="p-3.5 text-[#002147] font-sans font-extrabold">{log.action}</td>
                <td className="p-3.5 text-amber-800 font-bold">{log.resource}</td>
                <td className="p-3.5 text-slate-500">{log.ip_address}</td>
                <td className="p-3.5 text-right">
                  <span className="rounded bg-emerald-50 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-800 border border-emerald-200 font-sans">
                    {log.result}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
