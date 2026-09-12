import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendOrigin = process.env.SENTINEL_BACKEND_URL || "http://localhost:8000";
    return [{ source: "/api/v1/:path*", destination: `${backendOrigin}/api/v1/:path*` }];
  },
};

export default nextConfig;
