/**
 * GET /api/cctv/cameras — Proxy for cctv.corp8.cloud/cameras.json
 *
 * Authenticates with the CDN using session cookies managed server-side.
 * Returns the raw camera catalogue JSON to the browser.
 * Falls back to named Gujarat Police CCTV cameras if CDN is unreachable.
 */

import { NextRequest, NextResponse } from "next/server";
import { cdnFetch, hasCredentials, CDN_BASE } from "../auth";

export async function GET(request: NextRequest) {
  // No credentials — return rich named fallback cameras immediately
  if (!hasCredentials()) {
    return NextResponse.json(
      {
        status: "CCTV_CONFIG_MISSING",
        message: "CDN credentials not configured — showing demo cameras.",
        cameras: FALLBACK_CAMERAS,
        totalCount: FALLBACK_CAMERAS.length,
        source: "fallback",
      },
      { status: 200 }
    );
  }

  try {
    const response = await cdnFetch("/cameras.json");

    // Got login page instead of JSON
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      console.warn("[CCTV Catalogue] Got login page — auth failed");
      return NextResponse.json(
        {
          status: "AUTH_FAILED",
          message: "CDN authentication failed — showing demo cameras.",
          cameras: FALLBACK_CAMERAS,
          totalCount: FALLBACK_CAMERAS.length,
          source: "fallback",
        },
        { status: 200 }
      );
    }

    if (!response.ok) {
      return NextResponse.json(
        {
          status: "CDN_ERROR",
          message: `CDN returned status ${response.status}`,
          cameras: FALLBACK_CAMERAS,
          totalCount: FALLBACK_CAMERAS.length,
          source: "fallback",
        },
        { status: 200 }
      );
    }

    const data = await response.json();

    // Normalize: handle both array and {cameras: [...]} responses
    let cameras: any[];
    if (Array.isArray(data)) {
      cameras = data;
    } else if (data && typeof data === "object") {
      cameras = data.cameras || data.data || data.items || data.streams || data.list;
      if (!Array.isArray(cameras)) {
        cameras = data.id ? [data] : FALLBACK_CAMERAS;
      }
    } else {
      cameras = FALLBACK_CAMERAS;
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
        cameras: FALLBACK_CAMERAS,
        totalCount: FALLBACK_CAMERAS.length,
        source: "fallback",
      },
      { status: 200 }
    );
  }
}

// Named Gujarat Police CCTV demo cameras with real-world locations
const FALLBACK_CAMERAS = [
  { id: "cam01", name: "Ring Road Junction North", location: "Ahmedabad Central", zone: "GJ01", status: "online", latitude: 23.0225, longitude: 72.5714, type: "ANPR" },
  { id: "cam02", name: "SG Highway Express Gate 4", location: "Ahmedabad West", zone: "GJ01", status: "online", latitude: 23.09, longitude: 72.5342, type: "PTZ" },
  { id: "cam03", name: "Kalupur Station Entrance", location: "Ahmedabad East", zone: "GJ01", status: "online", latitude: 23.027, longitude: 72.6012, type: "FIXED" },
  { id: "cam04", name: "Majura Gate Circle", location: "Surat South", zone: "GJ05", status: "online", latitude: 21.1702, longitude: 72.8311, type: "ANPR" },
  { id: "cam05", name: "Sector 11 Secretariat Plaza", location: "Gandhinagar Govt Complex", zone: "GJ18", status: "online", latitude: 23.2156, longitude: 72.6369, type: "PTZ" },
  { id: "cam06", name: "Trikon Baug Junction", location: "Rajkot Center", zone: "GJ03", status: "degraded", latitude: 22.3039, longitude: 70.8022, type: "FIXED" },
  { id: "cam07", name: "Navrangpura Crossroads", location: "Ahmedabad Central", zone: "GJ01", status: "online", latitude: 23.0395, longitude: 72.5579, type: "PTZ" },
  { id: "cam08", name: "Vadodara Sayajigunj Gate", location: "Vadodara Central", zone: "GJ06", status: "online", latitude: 22.3072, longitude: 73.1812, type: "ANPR" },
  { id: "cam09", name: "Surat Diamond Naka", location: "Surat North", zone: "GJ05", status: "online", latitude: 21.2001, longitude: 72.8379, type: "FIXED" },
  { id: "cam10", name: "Kankaria Lake Entrance", location: "Ahmedabad South", zone: "GJ01", status: "online", latitude: 22.9965, longitude: 72.6036, type: "PTZ" },
  { id: "cam11", name: "Jamnagar Bedi Gate", location: "Jamnagar West", zone: "GJ10", status: "online", latitude: 22.4707, longitude: 70.0577, type: "FIXED" },
  { id: "cam12", name: "Bhavnagar Highway Toll", location: "Bhavnagar Range", zone: "GJ04", status: "online", latitude: 21.7645, longitude: 72.1519, type: "ANPR" },
  { id: "cam13", name: "ISCON Circle Overbridge", location: "Ahmedabad West", zone: "GJ01", status: "online", latitude: 23.0379, longitude: 72.5091, type: "PTZ" },
  { id: "cam14", name: "Anand Vidyanagar Road", location: "Anand District", zone: "GJ16", status: "online", latitude: 22.5645, longitude: 72.9289, type: "FIXED" },
  { id: "cam15", name: "Mehsana Highway Junction", location: "Mehsana North", zone: "GJ21", status: "online", latitude: 23.5979, longitude: 72.3693, type: "ANPR" },
  { id: "cam16", name: "Gandhinagar Sector 28 Gate", location: "Gandhinagar East", zone: "GJ18", status: "online", latitude: 23.2322, longitude: 72.6679, type: "FIXED" },
  { id: "cam17", name: "Sabarmati Riverfront South", location: "Ahmedabad Central", zone: "GJ01", status: "online", latitude: 23.0281, longitude: 72.5832, type: "PTZ" },
  { id: "cam18", name: "Rajkot Airport Road Gate", location: "Rajkot North", zone: "GJ03", status: "online", latitude: 22.3109, longitude: 70.7794, type: "ANPR" },
  { id: "cam19", name: "Morbi Rambaug Junction", location: "Morbi District", zone: "GJ27", status: "online", latitude: 22.8174, longitude: 70.8376, type: "FIXED" },
  { id: "cam20", name: "Surat Athwalines Central", location: "Surat Central", zone: "GJ05", status: "online", latitude: 21.1895, longitude: 72.8288, type: "PTZ" },
  { id: "cam21", name: "Patan Heritage Gate", location: "Patan District", zone: "GJ20", status: "online", latitude: 23.8493, longitude: 72.1266, type: "FIXED" },
  { id: "cam22", name: "Bharuch Causeway Camera", location: "Bharuch Range", zone: "GJ08", status: "online", latitude: 21.7051, longitude: 72.9959, type: "ANPR" },
  { id: "cam23", name: "Navsari Bus Terminal Gate", location: "Navsari District", zone: "GJ07", status: "online", latitude: 20.9467, longitude: 72.9520, type: "FIXED" },
  { id: "cam24", name: "Valsad Court Road Junction", location: "Valsad District", zone: "GJ17", status: "online", latitude: 20.6161, longitude: 72.9282, type: "PTZ" },
  { id: "cam25", name: "Kutch Bhuj Gate North", location: "Kutch District", zone: "GJ22", status: "online", latitude: 23.2419, longitude: 69.6669, type: "ANPR" },
  { id: "cam26", name: "Porbandar Nehru Gate", location: "Porbandar District", zone: "GJ11", status: "online", latitude: 21.6417, longitude: 69.6293, type: "FIXED" },
  { id: "cam27", name: "Amreli Highway Checkpoint", location: "Amreli District", zone: "GJ12", status: "online", latitude: 21.6032, longitude: 71.2213, type: "ANPR" },
  { id: "cam28", name: "Surendranagar Wadhwan Gate", location: "Surendranagar District", zone: "GJ24", status: "online", latitude: 22.7284, longitude: 71.6374, type: "FIXED" },
  { id: "cam29", name: "Gandhinagar State Highway 40", location: "Gandhinagar Outskirts", zone: "GJ18", status: "online", latitude: 23.1793, longitude: 72.6369, type: "PTZ" },
  { id: "cam30", name: "Ahmedabad Airport Road ANPR", location: "Ahmedabad North", zone: "GJ01", status: "online", latitude: 23.0732, longitude: 72.6347, type: "ANPR" },
];
