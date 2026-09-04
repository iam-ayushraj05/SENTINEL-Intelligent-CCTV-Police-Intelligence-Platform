"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  const isPublicLanding = pathname === "/" || pathname === "/login";

  if (isPublicLanding) {
    return <div className="w-full min-h-screen bg-[#eef6fb] text-slate-900">{children}</div>;
  }

  return (
    <div className="min-h-screen flex flex-col font-sans antialiased bg-[#eef6fb] text-slate-900">
      <Navbar />
      <div className="flex flex-1 w-full">
        <Sidebar />
        <main className="flex-1 p-4 md:p-6 overflow-y-auto max-w-full">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
