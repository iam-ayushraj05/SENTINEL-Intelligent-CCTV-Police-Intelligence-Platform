import "./globals.css";
import React from "react";
import { AppLayout } from "@/components/layout/AppLayout";

export const metadata = {
  title: "SENTINEL — Gujarat State Police Command & Control Centre",
  description: "Gujarat Police AI-powered unified CCTV surveillance, ANPR vehicle tracking & smart policing platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#eef6fb] text-slate-900 min-h-screen flex flex-col font-sans antialiased">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
