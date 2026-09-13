/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendOrigin =
      process.env.SENTINEL_BACKEND_URL || "http://localhost:8000";
    return [
      // Proxy all /api/v1/* to the FastAPI backend
      // Note: /api/cctv/* is handled by Next.js API routes (NOT proxied)
      {
        source: "/api/v1/:path*",
        destination: `${backendOrigin}/api/v1/:path*`,
      },
    ];
  },
  // Allow images from external sources
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "cctv.corp8.cloud" },
      { protocol: "https", hostname: "**.mux.dev" },
    ],
  },
};

export default nextConfig;
