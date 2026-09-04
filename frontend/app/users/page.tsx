"use client";

import React, { useEffect, useState } from "react";
import { User } from "@/lib/types";
import { api } from "@/lib/api";
import { Users, Shield, UserCheck, Lock } from "lucide-react";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    api.getUsers().then((data) => {
      if (data.length) setUsers(data);
      else {
        setUsers([
          {
            id: "u1",
            username: "admin",
            email: "admin@sentinel.police.gov.in",
            full_name: "Commanding Inspector General A. Sharma",
            role: "ADMIN",
            badge_number: "GJ-POL-001",
            is_active: true,
          },
          {
            id: "u2",
            username: "operator01",
            email: "operator01@sentinel.police.gov.in",
            full_name: "Sub-Inspector Rajesh Patel",
            role: "OPERATOR",
            badge_number: "GJ-POL-142",
            is_active: true,
          },
          {
            id: "u3",
            username: "investigator02",
            email: "investigator02@sentinel.police.gov.in",
            full_name: "Inspector Vikram Desai",
            role: "INVESTIGATOR",
            badge_number: "GJ-POL-089",
            is_active: true,
          },
        ]);
      }
    });
  }, []);

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header */}
      <div className="border-b border-slate-300 pb-4">
        <h1 className="text-2xl font-black tracking-tight text-[#002147] flex items-center gap-2">
          <Users className="h-6 w-6 text-[#0077b6]" />
          <span>POLICE PERSONNEL USER & ROLE MANAGEMENT</span>
        </h1>
        <p className="mt-1 text-xs text-slate-600 font-medium">Role-Based Access Control (RBAC) & Badged Session Audit Matrix</p>
      </div>

      {/* Users Table */}
      <div className="rounded-2xl border border-[#cbd5e1] bg-white overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-300 bg-[#f8fafc] text-slate-600 font-extrabold uppercase tracking-wider">
            <tr>
              <th className="p-3.5">Badge #</th>
              <th className="p-3.5">Officer Name</th>
              <th className="p-3.5">Username</th>
              <th className="p-3.5">Role</th>
              <th className="p-3.5">Official Email</th>
              <th className="p-3.5">Account Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-slate-700 font-medium">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-[#e2f1f8]/40 transition-colors">
                <td className="p-3.5 font-mono font-black text-[#0077b6]">{u.badge_number || "GJ-POL-N/A"}</td>
                <td className="p-3.5 font-extrabold text-[#002147]">{u.full_name}</td>
                <td className="p-3.5 font-mono text-slate-500 font-bold">{u.username}</td>
                <td className="p-3.5">
                  <span
                    className={`rounded px-2.5 py-0.5 text-[10px] font-extrabold uppercase ${
                      u.role === "ADMIN"
                        ? "bg-[#e2f1f8] text-[#0077b6] border border-[#bde0fe]"
                        : "bg-slate-100 text-slate-700 border border-slate-300"
                    }`}
                  >
                    {u.role}
                  </span>
                </td>
                <td className="p-3.5 font-mono text-slate-600">{u.email}</td>
                <td className="p-3.5">
                  <span className="rounded bg-emerald-50 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-800 border border-emerald-200">
                    ACTIVE
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
