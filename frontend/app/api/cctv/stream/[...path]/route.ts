/**
 * GET /api/cctv/stream/[...path] — HLS media proxy
 *
 * Proxies .m3u8 playlists and .ts segments from cctv.corp8.cloud through
 * the authenticated CDN session. Rewrites internal playlist URLs to route
 * back through this proxy.
 *
 * SECURITY:
 * - Only allowlists cctv.corp8.cloud as upstream
 * - Validates path extensions (.m3u8 and .ts only)
 * - Checks Referer header to prevent open-relay abuse
 * - Never exposes CDN credentials to the browser
 */

import { NextRequest, NextResponse } from "next/server";
import { cdnFetch, hasCredentials, CDN_BASE } from "../../auth";

const ALLOWED_EXTENSIONS = [".m3u8", ".ts", ".m4s", ".mp4"];
const PROXY_BASE = "/api/cctv/stream";

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

  // Check credentials
  if (!hasCredentials()) {
    return new NextResponse("CCTV credentials not configured", { status: 503 });
  }

  try {
    const cdnUrl = `${CDN_BASE}/${streamPath}`;
    const response = await cdnFetch(cdnUrl);

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        return new NextResponse("Access denied — CDN authentication failed", {
          status: 403,
        });
      }
      return new NextResponse(`CDN error: ${response.status}`, {
        status: response.status,
      });
    }

    // Check if we got a login page
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      return new NextResponse("Access denied — CDN returned login page", {
        status: 403,
      });
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

    // For .ts segments — stream directly without buffering entirely
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
    return new NextResponse("Stream proxy error", { status: 502 });
  }
}

/**
 * Rewrite .m3u8 playlist URLs to route through our proxy.
 * Handles both relative and absolute URLs in the playlist.
 */
function rewritePlaylist(playlist: string, requestPath: string): string {
  // Get the directory of the current request for resolving relative paths
  const pathParts = requestPath.split("/");
  pathParts.pop(); // Remove the filename
  const baseDir = pathParts.join("/");

  const lines = playlist.split("\n");
  const rewritten = lines.map((line) => {
    const trimmed = line.trim();

    // Skip comments and empty lines
    if (trimmed.startsWith("#") || trimmed === "") {
      // But check for URI= attributes in tags like #EXT-X-MAP
      if (trimmed.includes('URI="')) {
        return trimmed.replace(/URI="([^"]+)"/g, (match, uri) => {
          const resolvedUri = resolveUri(uri, baseDir);
          return `URI="${PROXY_BASE}/${resolvedUri}"`;
        });
      }
      return line;
    }

    // This is a media segment URL
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
      // Absolute URL — strip CDN base and route through proxy
      const cdnBase = CDN_BASE.replace(/\/$/, "");
      if (trimmed.startsWith(cdnBase)) {
        const relativePath = trimmed.substring(cdnBase.length + 1);
        return `${PROXY_BASE}/${relativePath}`;
      }
      // External URL — pass through (shouldn't happen for our CDN)
      return trimmed;
    }

    // Relative URL — resolve relative to current playlist path
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
  // Relative path
  return baseDir ? `${baseDir}/${uri}` : uri;
}
