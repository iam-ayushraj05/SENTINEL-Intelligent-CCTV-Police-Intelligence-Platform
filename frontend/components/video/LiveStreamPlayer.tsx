"use client";

import React, { useState, useEffect, useRef } from "react";
import { Camera } from "@/lib/types";
import { Camera as CameraIcon, Eye, EyeOff, Maximize, Play, RefreshCw } from "lucide-react";

interface Props {
  camera: Camera;
  showOverlayDefault?: boolean;
}

export const LiveStreamPlayer: React.FC<Props> = ({ camera, showOverlayDefault = true }) => {
  const [showOverlays, setShowOverlays] = useState(showOverlayDefault);
  const [fps, setFps] = useState(25);
  const [latency, setLatency] = useState(38);
  const [isSnapshotting, setIsSnapshotting] = useState(false);
  const [snapshotMsg, setSnapshotMsg] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Simulated moving object tracks
  const tracksRef = useRef([
    { x: 120, y: 150, w: 180, h: 110, label: "car 0.96 [TRK-102]", color: "#3b82f6", plate: "GJ05CD5678", dx: 1.2, dy: 0.3 },
    { x: 420, y: 220, w: 70, h: 160, label: "person 0.91 [TRK-204]", color: "#10b981", plate: null, dx: -0.6, dy: 0.2 },
    { x: 300, y: 110, w: 140, h: 90, label: "motorcycle 0.88 [TRK-305]", color: "#f59e0b", plate: null, dx: 0.9, dy: -0.1 },
  ]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frameCount = 0;
    let lastTime = performance.now();

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Draw simulated camera background (dark CCTV road environment)
      ctx.fillStyle = "#091424";
      ctx.fillRect(0, 0, width, height);

      // Draw road / lane markings
      ctx.strokeStyle = "#1e2f47";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(width * 0.2, height);
      ctx.lineTo(width * 0.45, height * 0.4);
      ctx.moveTo(width * 0.8, height);
      ctx.lineTo(width * 0.55, height * 0.4);
      ctx.stroke();

      // Dashed lane center
      ctx.setLineDash([15, 15]);
      ctx.strokeStyle = "#334b6e";
      ctx.beginPath();
      ctx.moveTo(width * 0.5, height);
      ctx.lineTo(width * 0.5, height * 0.4);
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw simulated camera timestamp header
      const now = new Date();
      ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
      ctx.fillRect(10, 10, 320, 34);
      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 12px monospace";
      ctx.fillText(`${camera.camera_code} | ${camera.name}`, 18, 26);
      ctx.fillStyle = "#94a3b8";
      ctx.fillText(now.toISOString().replace("T", " ").substring(0, 19), 18, 38);

      // Update & Draw Bounding Boxes if overlay is ON
      if (showOverlays) {
        tracksRef.current.forEach((trk) => {
          trk.x += trk.dx;
          trk.y += trk.dy;
          if (trk.x > width - 100 || trk.x < 50) trk.dx *= -1;
          if (trk.y > height - 100 || trk.y < 50) trk.dy *= -1;

          // Draw Bounding Box
          ctx.strokeStyle = trk.color;
          ctx.lineWidth = 2;
          ctx.strokeRect(trk.x, trk.y, trk.w, trk.h);

          // Draw Corner Accents
          const cornerLen = 10;
          ctx.lineWidth = 3;
          ctx.beginPath();
          // Top Left
          ctx.moveTo(trk.x, trk.y + cornerLen); ctx.lineTo(trk.x, trk.y); ctx.lineTo(trk.x + cornerLen, trk.y);
          // Top Right
          ctx.moveTo(trk.x + trk.w - cornerLen, trk.y); ctx.lineTo(trk.x + trk.w, trk.y); ctx.lineTo(trk.x + trk.w, trk.y + cornerLen);
          ctx.stroke();

          // Label Box
          ctx.fillStyle = trk.color;
          ctx.fillRect(trk.x, trk.y - 22, ctx.measureText(trk.label).width + 16, 22);

          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 11px sans-serif";
          ctx.fillText(trk.label, trk.x + 6, trk.y - 7);

          // ANPR Plate Callout
          if (trk.plate) {
            ctx.fillStyle = "#f43f5e";
            ctx.fillRect(trk.x, trk.y + trk.h + 4, 140, 20);
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 11px monospace";
            ctx.fillText(`PLATE: ${trk.plate}`, trk.x + 6, trk.y + trk.h + 18);
          }
        });
      }

      // FPS calculation
      frameCount++;
      const currentTime = performance.now();
      if (currentTime - lastTime >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        lastTime = currentTime;
      }

      animationRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [camera, showOverlays]);

  const handleSnapshot = () => {
    setIsSnapshotting(true);
    setSnapshotMsg("Evidence Frame Captured & Hash Computed");
    setTimeout(() => {
      setIsSnapshotting(false);
      setSnapshotMsg(null);
    }, 2500);
  };

  return (
    <div className="relative overflow-hidden rounded-xl border border-[var(--border)] bg-[#050c17] shadow-lg">
      {/* Top Video Control Overlay */}
      <div className="absolute top-3 right-3 z-20 flex items-center gap-2">
        <span className="rounded bg-black/70 px-2 py-1 text-[10px] font-bold text-amber-300 border border-amber-800/80">
          DEMO STREAM
        </span>
        <span className="rounded bg-black/70 px-2 py-1 text-[10px] font-mono text-emerald-400 border border-slate-700">
          {fps} FPS | {latency}ms
        </span>
        <button
          onClick={() => setShowOverlays(!showOverlays)}
          className={`flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-semibold backdrop-blur transition-all ${
            showOverlays
              ? "bg-indigo-600/90 text-white border border-indigo-400"
              : "bg-black/70 text-slate-400 border border-slate-700 hover:text-white"
          }`}
        >
          {showOverlays ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
          <span>AI Overlays</span>
        </button>
        <button
          onClick={handleSnapshot}
          className="flex items-center gap-1 rounded bg-black/70 px-2.5 py-1 text-xs font-semibold text-slate-200 border border-slate-700 hover:bg-slate-800 transition-colors"
          title="Capture Evidence Frame"
        >
          <CameraIcon className="h-3.5 w-3.5 text-indigo-400" />
          <span>Snapshot</span>
        </button>
      </div>

      {snapshotMsg && (
        <div className="absolute top-14 right-3 z-30 rounded-lg bg-emerald-950/90 border border-emerald-700 px-3 py-1.5 text-xs font-bold text-emerald-200 shadow-xl animate-fade-in">
          ✓ {snapshotMsg}
        </div>
      )}

      {/* Canvas Video Surface */}
      <canvas ref={canvasRef} width={640} height={360} className="w-full h-auto block object-cover" />

      {/* Bottom Bar Info */}
      <div className="flex items-center justify-between border-t border-[var(--border)] bg-[var(--panel)] px-4 py-2 text-xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-bold text-slate-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            {camera.name}
          </span>
          <span className="text-slate-500 font-mono">[{camera.camera_code}]</span>
        </div>
        <div className="flex items-center gap-3 text-slate-400 text-[11px]">
          <span>Zone: {camera.zone || "General"}</span>
          <span>Protocol: {camera.protocol}</span>
          <span className="text-indigo-400 font-semibold">Model: {camera.camera_type}</span>
        </div>
      </div>
    </div>
  );
};
