/**
 * GET /api/cctv/stream/[...path] — HLS media proxy
 *
 * When CDN credentials are configured & reachable: proxies .m3u8 playlists and .ts segments
 * from cctv.corp8.cloud through the authenticated CDN session.
 *
 * When CDN is unreachable or credentials are missing/invalid: serves a public HLS demo stream
 * with absolute segment URLs so hls.js can load segments directly without 302 redirect loops.
 */

import { NextRequest, NextResponse } from "next/server";
import { cdnFetch, hasCredentials, CDN_BASE } from "../../auth";

const ALLOWED_EXTENSIONS = [".m3u8", ".ts", ".m4s", ".mp4"];
const PROXY_BASE = "/api/cctv/stream";

async function serveDemoStream() {
  try {
    const demoMuxUrl = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8";
    const res = await fetch(demoMuxUrl, { cache: "no-store" });
    if (!res.ok) {
      return new NextResponse("Demo stream fetch failed", { status: 502 });
    }
    const text = await res.text();
    const baseUrl = "https://test-streams.mux.dev/x36xhzz/";

    // Rewrite relative URLs to absolute Mux URLs so hls.js fetches child playlists/segments directly
    const lines = text.split("\n");
    const rewritten = lines.map((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("#") || trimmed === "") return line;
      if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) return trimmed;
      return `${baseUrl}${trimmed}`;
    });

    return new NextResponse(rewritten.join("\n"), {
      status: 200,
      headers: {
        "Content-Type": "application/vnd.apple.mpegurl",
        "Cache-Control": "no-cache, no-store",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    return new NextResponse("Demo stream error", { status: 500 });
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const pathSegments = params.path;
  if (!pathSegments || pathSegments.length === 0) {
    return NextResponse.json({ error: "Missing stream path" }, { status: 400 });
  }

  const streamPath = pathSegments.join("/");

  // Validate extension
  const hasValidExt = ALLOWED_EXTENSIONS.some((ext) =>
    streamPath.toLowerCase().endsWith(ext)
  );
  if (!hasValidExt) {
    return NextResponse.json(
      { error: "Invalid resource type — only HLS playlists and segments are allowed" },
      { status: 403 }
    );
  }

  // If no CDN credentials, serve demo stream
  if (!hasCredentials()) {
    if (streamPath.toLowerCase().endsWith(".m3u8")) {
      return serveDemoStream();
    }
    return new NextResponse("No CDN configured", { status: 204 });
  }

  try {
    const cdnUrl = `${CDN_BASE}/${streamPath}`;
    const response = await cdnFetch(cdnUrl);

    if (!response.ok) {
      if (streamPath.toLowerCase().endsWith(".m3u8")) {
        return serveDemoStream();
      }
      return new NextResponse(`CDN error: ${response.status}`, {
        status: response.status,
      });
    }

    // Check if we got a login page
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      if (streamPath.toLowerCase().endsWith(".m3u8")) {
        return serveDemoStream();
      }
      return new NextResponse("Access denied — CDN returned login page", { status: 403 });
    }

    // For .m3u8 playlists — rewrite internal URLs to go through our proxy
    if (streamPath.toLowerCase().endsWith(".m3u8")) {
      const playlistText = await response.text();
      const rewritten = rewritePlaylist(playlistText, streamPath);

      return new NextResponse(rewritten, {
        status: 200,
        headers: {
          "Content-Type": "application/vnd.apple.mpegurl",
          "Cache-Control": "no-cache, no-store",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    // For .ts segments — stream directly
    const body = response.body;
    if (!body) {
      return new NextResponse("Empty segment", { status: 204 });
    }

    return new NextResponse(body, {
      status: 200,
      headers: {
        "Content-Type": "video/mp2t",
        "Cache-Control": "public, max-age=5",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (error) {
    console.error("[CCTV Stream] Proxy error:", (error as Error).message);
    if (streamPath.toLowerCase().endsWith(".m3u8")) {
      return serveDemoStream();
    }
    return new NextResponse("Stream proxy error", { status: 502 });
  }
}

function rewritePlaylist(playlist: string, requestPath: string): string {
  const pathParts = requestPath.split("/");
  pathParts.pop();
  const baseDir = pathParts.join("/");

  const lines = playlist.split("\n");
  const rewritten = lines.map((line) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("#") || trimmed === "") {
      if (trimmed.includes('URI="')) {
        return trimmed.replace(/URI="([^"]+)"/g, (match, uri) => {
          const resolvedUri = resolveUri(uri, baseDir);
          return `URI="${PROXY_BASE}/${resolvedUri}"`;
        });
      }
      return line;
    }

    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
      const cdnBase = CDN_BASE.replace(/\/$/, "");
      if (trimmed.startsWith(cdnBase)) {
        const relativePath = trimmed.substring(cdnBase.length + 1);
        return `${PROXY_BASE}/${relativePath}`;
      }
      return trimmed;
    }

    const resolvedPath = resolveUri(trimmed, baseDir);
    return `${PROXY_BASE}/${resolvedPath}`;
  });

  return rewritten.join("\n");
}

function resolveUri(uri: string, baseDir: string): string {
  if (uri.startsWith("/")) {
    return uri.substring(1);
  }
  if (uri.startsWith("http://") || uri.startsWith("https://")) {
    const cdnBase = CDN_BASE.replace(/\/$/, "");
    if (uri.startsWith(cdnBase)) {
      return uri.substring(cdnBase.length + 1);
    }
    return uri;
  }
  return baseDir ? `${baseDir}/${uri}` : uri;
}
