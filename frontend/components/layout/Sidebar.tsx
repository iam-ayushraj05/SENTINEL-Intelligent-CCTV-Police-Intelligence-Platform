"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  LayoutDashboard,
  Video,
  Bell,
  MapPin,
  Car,
  UserCheck,
  Briefcase,
  Eye,
  Search,
  Activity,
  Users,
  FileText,
  LogOut,
  AlertTriangle,
  Map,
  FolderLock,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Command Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Live Cameras", href: "/cameras", icon: Video },
  { label: "Alerts Center", href: "/alerts", icon: Bell, badge: "3" },
  { label: "🚨 Emergency Response", href: "/emergency", icon: AlertTriangle, badge: "NEW" },
  { label: "📹 Multi-Camera Monitor", href: "/emergency-cameras", icon: Map },
  { label: "GIS Operations Map", href: "/map", icon: MapPin },
  { label: "Vehicle Intelligence", href: "/vehicles", icon: Car },
  { label: "Person Intelligence", href: "/persons", icon: UserCheck },
  { label: "Investigations", href: "/investigations", icon: Briefcase },
  { label: "Watchlists", href: "/watchlists", icon: Eye },
  { label: "Global Search", href: "/search", icon: Search },
  { label: "Document Centre", href: "/documents", icon: FolderLock },
  { label: "System Health", href: "/system", icon: Activity },
  { label: "User Management", href: "/users", icon: Users },
  { label: "Audit Logs", href: "/audit", icon: FileText },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await api.logout();
    router.push("/");
  };

  return (
    <aside className="w-[240px] shrink-0 border-r border-[#cbd5e1] bg-white hidden md:flex flex-col justify-between py-3 px-2 min-h-[calc(100vh-3.5rem)] shadow-sm">
      <div className="space-y-1">
        <p className="px-3 text-[9px] font-extrabold tracking-widest uppercase text-slate-500 mb-2">
          COMMAND MODULES
        </p>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between rounded-md px-3 py-2 text-xs font-semibold transition-all ${
                isActive
                  ? "bg-[#e2f1f8] text-[#0077b6] border-l-4 border-[#0077b6] font-extrabold shadow-sm"
                  : "text-slate-700 hover:bg-[#f1f5f9] hover:text-[#002147]"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`h-4 w-4 ${isActive ? "text-[#0077b6]" : "text-slate-500"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="rounded-full bg-rose-600 px-1.5 py-0.2 text-[9px] font-black text-white">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      <div className="space-y-2 pt-2 border-t border-slate-200">
        <div className="rounded-md border border-[#bde0fe] bg-[#e2f1f8] p-2.5 text-xs">
          <p className="text-[9px] font-extrabold text-slate-500 uppercase tracking-widest">COMMAND NODE</p>
          <p className="mt-0.5 font-extrabold text-[#002147] text-[11px]">Gujarat State Police HQ</p>
          <p className="text-[10px] text-slate-600 mt-0.5 flex items-center justify-between">
            <span>AI Pipeline:</span>
            <span className="text-[#059669] font-extrabold">28.5 FPS</span>
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-1.5 rounded-md border border-rose-200 bg-rose-50 py-2 text-[11px] font-bold text-rose-700 hover:bg-rose-100 hover:text-rose-900 transition-colors shadow-sm active:scale-[0.98]"
          title="Logout & Return to Home Page"
        >
          <LogOut className="h-3.5 w-3.5 text-rose-600" />
          <span>Logout & Exit Home</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
