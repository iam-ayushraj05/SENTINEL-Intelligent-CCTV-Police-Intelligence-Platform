/**
 * GET /api/cctv/cameras — Proxy for cctv.corp8.cloud/cameras.json
 *
 * Authenticates with the CDN using session cookies managed server-side.
 * Returns the raw camera catalogue JSON to the browser.
 * Falls back to a static cam01-cam30 list if the CDN is unreachable.
 */

import { NextRequest, NextResponse } from "next/server";
import { cdnFetch, hasCredentials, CDN_BASE } from "../auth";

export async function GET(request: NextRequest) {
  // Check credentials are configured
  if (!hasCredentials()) {
    return NextResponse.json(
      {
        status: "CCTV_CONFIG_MISSING",
        message: "CDN credentials not configured on the server.",
        cameras: generateFallbackCameras(),
        source: "fallback",
      },
      { status: 200 }
    );
  }

  try {
    const response = await cdnFetch("/cameras.json");

    // Check if we got the login page instead of JSON
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      console.warn("[CCTV Catalogue] Got login page instead of JSON — auth may have failed");
      return NextResponse.json(
        {
          status: "AUTH_FAILED",
          message: "CDN authentication failed — check credentials.",
          cameras: generateFallbackCameras(),
          source: "fallback",
        },
        { status: 200 }
      );
    }

    if (!response.ok) {
      console.warn("[CCTV Catalogue] CDN returned status:", response.status);
      return NextResponse.json(
        {
          status: "CDN_ERROR",
          message: `CDN returned status ${response.status}`,
          cameras: generateFallbackCameras(),
          source: "fallback",
        },
        { status: 200 }
      );
    }

    const data = await response.json();

    // Normalize: handle both array and {cameras: [...]} responses
    let cameras;
    if (Array.isArray(data)) {
      cameras = data;
    } else if (data && typeof data === "object") {
      cameras =
        data.cameras || data.data || data.items || data.streams || data.list;
      if (!Array.isArray(cameras)) {
        // Single camera object or unknown format
        cameras = data.id ? [data] : [];
      }
    } else {
      cameras = [];
    }

    return NextResponse.json({
      status: "OK",
      cameras,
      totalCount: cameras.length,
      source: "cdn",
      fetchedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("[CCTV Catalogue] Fetch error:", (error as Error).message);
    return NextResponse.json(
      {
        status: "FETCH_ERROR",
        message: (error as Error).message,
        cameras: generateFallbackCameras(),
        source: "fallback",
      },
      { status: 200 }
    );
  }
}

function generateFallbackCameras() {
  return Array.from({ length: 30 }, (_, i) => ({
    id: `cam${String(i + 1).padStart(2, "0")}`,
    name: `CAM${String(i + 1).padStart(2, "0")}`,
    location: "Gujarat Range",
    status: "online",
  }));
}
