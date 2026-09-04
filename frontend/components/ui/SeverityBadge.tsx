import React from "react";
import { Severity } from "@/lib/types";

interface Props {
  severity: Severity | string;
}

export const SeverityBadge: React.FC<Props> = ({ severity }) => {
  const sev = (severity || "LOW").toUpperCase();
  
  let colors = "bg-blue-950/80 text-blue-300 border-blue-800/60";
  if (sev === "MEDIUM") {
    colors = "bg-amber-950/80 text-amber-300 border-amber-800/60";
  } else if (sev === "HIGH") {
    colors = "bg-orange-950/80 text-orange-300 border-orange-800/60";
  } else if (sev === "CRITICAL") {
    colors = "bg-red-950/90 text-red-400 border-red-800 animate-pulse font-bold";
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs tracking-wider uppercase ${colors}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${sev === "CRITICAL" ? "bg-red-500" : sev === "HIGH" ? "bg-orange-500" : sev === "MEDIUM" ? "bg-amber-500" : "bg-blue-400"}`} />
      {sev}
    </span>
  );
};
