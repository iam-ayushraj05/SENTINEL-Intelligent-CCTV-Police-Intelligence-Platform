import React from "react";
import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: string;
  badge?: string;
  badgeColor?: "red" | "amber" | "green" | "blue";
}

export const StatCard: React.FC<Props> = ({ title, value, subtitle, icon: Icon, badge, badgeColor = "blue" }) => {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-[#cbd5e1] bg-white p-5 shadow-sm transition-all hover:border-[#0077b6]">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">{title}</span>
        {Icon && <Icon className="h-5 w-5 text-[#0077b6]" />}
      </div>
      <div className="mt-3 flex items-baseline justify-between">
        <p className="text-2xl font-black tracking-tight text-[#002147]">{value}</p>
        {badge && (
          <span
            className={`rounded px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider border ${
              badgeColor === "red"
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : badgeColor === "amber"
                ? "bg-amber-50 text-amber-800 border-amber-200"
                : badgeColor === "green"
                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                : "bg-sky-50 text-sky-800 border-sky-200"
            }`}
          >
            {badge}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-2 text-xs font-medium text-slate-600">{subtitle}</p>}
    </div>
  );
};
