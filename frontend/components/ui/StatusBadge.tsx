import React from "react";
import { CameraStatus, AlertStatus } from "@/lib/types";

interface Props {
  status: CameraStatus | AlertStatus | string;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const st = (status || "UNKNOWN").toUpperCase();

  let colors = "bg-slate-800 text-slate-300 border-slate-700";
  if (st === "ONLINE" || st === "RESOLVED") {
    colors = "bg-emerald-950/80 text-emerald-300 border-emerald-800/60";
  } else if (st === "OFFLINE" || st === "DISMISSED") {
    colors = "bg-rose-950/80 text-rose-300 border-rose-800/60";
  } else if (st === "DEGRADED" || st === "ACKNOWLEDGED" || st === "INVESTIGATING") {
    colors = "bg-amber-950/80 text-amber-300 border-amber-800/60";
  } else if (st === "OPEN") {
    colors = "bg-blue-950/80 text-blue-300 border-blue-800/60";
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-medium uppercase tracking-wider ${colors}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${st === "ONLINE" || st === "RESOLVED" ? "bg-emerald-400" : st === "OFFLINE" ? "bg-rose-500" : "bg-amber-400"}`} />
      {st}
    </span>
  );
};
