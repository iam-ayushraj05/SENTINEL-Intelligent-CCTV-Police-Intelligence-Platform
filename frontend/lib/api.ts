import {
  Camera,
  Alert,
  Detection,
  VehicleIntelligence,
  Investigation,
  Watchlist,
  WatchlistEntry,
  AuditLogItem,
  DashboardSummary,
  User,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const isMultipart = typeof FormData !== "undefined" && options?.body instanceof FormData;
    const accessToken = typeof window !== "undefined" ? sessionStorage.getItem("sentinel_access_token") : null;
    const res = await fetch(`${API_BASE}${endpoint}`, {
      credentials: "include",
      headers: {
        ...(isMultipart ? {} : { "Content-Type": "application/json" }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...options?.headers,
      },
      ...options,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const payload = await res.json();
        const structuredDetail = payload.detail;
        detail = typeof structuredDetail === "string"
          ? structuredDetail
          : structuredDetail?.message || payload.message || detail;
      } catch {
        // Keep the HTTP status when the server did not return JSON.
      }
      throw new Error(`API Error ${res.status}: ${detail}`);
    }
    return await res.json();
  } catch (err) {
    console.warn(`API call ${endpoint} failed:`, err);
    if (err instanceof TypeError) {
      throw new Error("SENTINEL API is unavailable. Check the application connection and try again.");
    }
    throw err;
  }
}

export const fetchAPI = fetcher;

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const result = await fetcher<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    if (typeof window !== "undefined" && result.access_token) {
      sessionStorage.setItem("sentinel_access_token", result.access_token);
    }
    return result;
  },
  getCurrentUser: () => fetcher<User>("/auth/me"),
  logout: async () => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("sentinel_access_token");
    }
  },

  // Cameras
  getCameras: () => fetcher<Camera[]>("/cameras").catch(() => MOCK_CAMERAS),
  getCamera: (id: string) => fetcher<Camera>(`/cameras/${id}`).catch(() => MOCK_CAMERAS.find((c) => c.id === id) || MOCK_CAMERAS[0]),
  createCamera: (data: Partial<Camera>) =>
    fetcher<Camera>("/cameras", { method: "POST", body: JSON.stringify(data) }),
  updateCamera: (id: string, data: Partial<Camera>) =>
    fetcher<Camera>(`/cameras/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCamera: (id: string) => fetcher<{ message: string }>(`/cameras/${id}`, { method: "DELETE" }),

  // Alerts
  getAlerts: (severity?: string, status?: string) => {
    const params = new URLSearchParams();
    if (severity) params.set("severity", severity);
    if (status) params.set("status", status);
    const query = params.toString() ? `?${params.toString()}` : "";
    return fetcher<Alert[]>(`/alerts${query}`).catch(() => MOCK_ALERTS);
  },
  getAlert: (id: string) => fetcher<Alert>(`/alerts/${id}`).catch(() => MOCK_ALERTS.find((a) => a.id === id) || MOCK_ALERTS[0]),
  updateAlertStatus: (id: string, status: string, notes?: string) =>
    fetcher<Alert>(`/alerts/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status, notes }),
    }),
  acknowledgeAlert: (id: string, officerName?: string) =>
    fetcher<Alert>(`/alerts/${id}/acknowledge`, {
      method: "POST",
      body: JSON.stringify({ officer_name: officerName || "Operator" }),
    }).catch(() => ({ ...(MOCK_ALERTS.find((a) => a.id === id) || MOCK_ALERTS[0]), status: "ACKNOWLEDGED" as AlertStatus })),
  resolveAlert: (id: string, notes?: string) =>
    fetcher<Alert>(`/alerts/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    }).catch(() => ({ ...(MOCK_ALERTS.find((a) => a.id === id) || MOCK_ALERTS[0]), status: "RESOLVED" as AlertStatus })),

  // Detections & AI
  getDetections: (camera_id?: string) =>
    fetcher<Detection[]>(`/detections${camera_id ? `?camera_id=${camera_id}` : ""}`).catch(() => MOCK_DETECTIONS),

  // Vehicles & ANPR
  getVehicleIntelligence: (plate: string, from_time?: string, to_time?: string) =>
    fetcher<VehicleIntelligence>(`/vehicles/${plate}${from_time || to_time ? `?${new URLSearchParams({ ...(from_time ? { from_time } : {}), ...(to_time ? { to_time } : {}) }).toString()}` : ""}`).catch(() => ({
      plate_number: plate,
      normalized_plate: plate.replace(/[^A-Z0-9]/gi, "").toUpperCase(),
      vehicle_type: "Sedan",
      color: "White",
      make_model: "Hyundai Verna",
      stolen_flag: true,
      wanted_flag: false,
      owner_name: "Ramesh Patel",
      owner_phone: "+91 9876543210",
      registration_date: "2021-05-14",
      rto_location: "Ahmedabad RTO (GJ-01)",
      metadata_json: {
        chassis_number: "MBHABC1234567890",
        engine_number: "ENG987654321",
        insurance_status: "ACTIVE",
        puc_valid_until: "2026-12-31",
      },
      total_sightings: 3,
      sightings: [
        {
          id: "s1",
          camera_id: MOCK_CAMERAS[0].id,
          camera_name: MOCK_CAMERAS[0].name,
          timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
          confidence: 0.96,
          latitude: 23.0225,
          longitude: 72.5714,
          vehicle_type: "car",
          color: "Silver",
          evidence_url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
        },
        {
          id: "s2",
          camera_id: MOCK_CAMERAS[1].id,
          camera_name: MOCK_CAMERAS[1].name,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          confidence: 0.94,
          latitude: 23.09,
          longitude: 72.5342,
          vehicle_type: "car",
          color: "Silver",
          evidence_url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
        },
      ],
      watchlist_matches: [{ id: "w1", priority: "HIGH", source_system: "VAHAN_POLICE_FIR" }],
      registered_owner: {
        owner_name: "Suresh Shah",
        registration_date: "2019-11-20",
        rto_location: "Surat RTO (GJ-05)",
        stolen_status: "FLAGGED_STOLEN",
      },
    })),
  getVehicleRoute: (plate: string) => fetcher<any>(`/vehicles/${plate}/route`).catch(() => ({ plate, segments: [] })),
  getDeletedVehicles: () => fetcher<Array<{ id: string; plate: string; deleted_at: string | null; metadata_json?: Record<string, any> }>>("/vehicles/deleted"),

  // Watchlists
  getWatchlists: () => fetcher<Watchlist[]>("/watchlists").catch(() => MOCK_WATCHLISTS),
  createWatchlist: (data: Partial<Watchlist>) =>
    fetcher<Watchlist>("/watchlists", { method: "POST", body: JSON.stringify(data) }),
  getWatchlistEntries: (id: string) =>
    fetcher<WatchlistEntry[]>(`/watchlists/${id}/entries`).catch(() => MOCK_WATCHLIST_ENTRIES),
  addWatchlistEntry: (id: string, data: Partial<WatchlistEntry>) =>
    fetcher<WatchlistEntry>(`/watchlists/${id}/entries`, { method: "POST", body: JSON.stringify(data) }),

  // Investigations
  getInvestigations: () => fetcher<Investigation[]>("/investigations").catch(() => MOCK_INVESTIGATIONS),
  getInvestigation: (id: string) =>
    fetcher<Investigation>(`/investigations/${id}`).catch(() => MOCK_INVESTIGATIONS[0]),
  createInvestigation: (data: { title: string; description?: string; assigned_officer_name?: string }) =>
    fetcher<Investigation>("/investigations", { method: "POST", body: JSON.stringify(data) }),
  addInvestigationNote: (id: string, note: string, author?: string) =>
    fetcher<any>(`/investigations/${id}/notes`, {
      method: "POST",
      body: JSON.stringify({ note, author }),
    }),
  getPersons: (search?: string) => fetcher<Array<Record<string, unknown>>>(`/persons${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  createPerson: (data: Record<string, unknown>) => fetcher<{ id: string; person_code: string; case_id: string; status: string }>("/persons", { method: "POST", body: JSON.stringify(data) }),
  createPersonIntake: (data: { full_name: string; alias?: string; date_of_birth?: string; gender?: string; agency_unit?: string; phone_number?: string; address?: string; case_title: string; case_notes?: string; photo?: File }) => {
    const body = new FormData();
    Object.entries(data).forEach(([key, value]) => { if (value !== undefined && value !== "") body.append(key, value instanceof File ? value : String(value)); });
    return fetcher<{ id: string; person_code: string; case_id: string; status: string }>("/persons/intake", { method: "POST", body });
  },
  uploadPersonPhoto: (id: string, photo: File) => {
    const body = new FormData();
    body.append("photo", photo);
    return fetcher<{ photo_url: string }>(`/persons/${id}/photo`, { method: "POST", body, headers: {} });
  },

  // Government & Search & Audit & Simulator
  lookupGovernmentVehicle: (plate_number: string) =>
    fetcher<any>("/government/vehicle-lookup", {
      method: "POST",
      body: JSON.stringify({ plate_number }),
    }),
  globalSearch: (q: string) => fetcher<any>(`/search?q=${encodeURIComponent(q)}`),
  getAuditLogs: () => fetcher<AuditLogItem[]>("/audit-logs").catch(() => MOCK_AUDIT_LOGS),
  triggerDemoEvent: (event_type: string, plate_number?: string) =>
    fetcher<any>("/simulator/trigger-event", {
      method: "POST",
      body: JSON.stringify({ event_type, plate_number }),
    }),
};

// 30 Named Gujarat Police CCTV Cameras
export const MOCK_CAMERAS: Camera[] = [
  { id: "cam01", camera_code: "CAM01", name: "Ring Road Junction North", zone: "Gujarat Range", camera_type: "ANPR", latitude: 23.0225, longitude: 72.5714, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam01/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam02", camera_code: "CAM02", name: "SG Highway Express Gate 4", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.0900, longitude: 72.5342, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam02/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam03", camera_code: "CAM03", name: "Kalupur Station Entrance", zone: "Gujarat Range", camera_type: "FIXED", latitude: 23.0270, longitude: 72.6012, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam03/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam04", camera_code: "CAM04", name: "Majura Gate Circle", zone: "Gujarat Range", camera_type: "ANPR", latitude: 21.1702, longitude: 72.8311, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam04/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam05", camera_code: "CAM05", name: "Sector 11 Secretariat Plaza", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.2156, longitude: 72.6369, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam05/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam06", camera_code: "CAM06", name: "Trikon Baug Junction", zone: "Gujarat Range", camera_type: "FIXED", latitude: 22.3039, longitude: 70.8022, status: "DEGRADED", is_active: true, stream_url: "/api/cctv/stream/cam06/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam07", camera_code: "CAM07", name: "Navrangpura Crossroads", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.0395, longitude: 72.5579, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam07/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam08", camera_code: "CAM08", name: "Vadodara Sayajigunj Gate", zone: "Gujarat Range", camera_type: "ANPR", latitude: 22.3072, longitude: 73.1812, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam08/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam09", camera_code: "CAM09", name: "Surat Diamond Naka", zone: "Gujarat Range", camera_type: "FIXED", latitude: 21.2001, longitude: 72.8379, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam09/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam10", camera_code: "CAM10", name: "Kankaria Lake Entrance", zone: "Gujarat Range", camera_type: "PTZ", latitude: 22.9965, longitude: 72.6036, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam10/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam11", camera_code: "CAM11", name: "Jamnagar Bedi Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 22.4707, longitude: 70.0577, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam11/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam12", camera_code: "CAM12", name: "Bhavnagar Highway Toll", zone: "Gujarat Range", camera_type: "ANPR", latitude: 21.7645, longitude: 72.1519, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam12/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam13", camera_code: "CAM13", name: "ISCON Circle Overbridge", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.0379, longitude: 72.5091, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam13/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam14", camera_code: "CAM14", name: "Anand Vidyanagar Road", zone: "Gujarat Range", camera_type: "FIXED", latitude: 22.5645, longitude: 72.9289, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam14/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam15", camera_code: "CAM15", name: "Mehsana Highway Junction", zone: "Gujarat Range", camera_type: "ANPR", latitude: 23.5979, longitude: 72.3693, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam15/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam16", camera_code: "CAM16", name: "Gandhinagar Sector 28 Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 23.2322, longitude: 72.6679, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam16/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam17", camera_code: "CAM17", name: "Sabarmati Riverfront South", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.0281, longitude: 72.5832, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam17/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam18", camera_code: "CAM18", name: "Rajkot Airport Road Gate", zone: "Gujarat Range", camera_type: "ANPR", latitude: 22.3109, longitude: 70.7794, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam18/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam19", camera_code: "CAM19", name: "Morbi Rambaug Junction", zone: "Gujarat Range", camera_type: "FIXED", latitude: 22.8174, longitude: 70.8376, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam19/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam20", camera_code: "CAM20", name: "Surat Athwalines Central", zone: "Gujarat Range", camera_type: "PTZ", latitude: 21.1895, longitude: 72.8288, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam20/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam21", camera_code: "CAM21", name: "Patan Heritage Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 23.8493, longitude: 72.1266, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam21/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam22", camera_code: "CAM22", name: "Bharuch Causeway Camera", zone: "Gujarat Range", camera_type: "ANPR", latitude: 21.7051, longitude: 72.9959, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam22/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam23", camera_code: "CAM23", name: "Navsari Bus Terminal Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 20.9467, longitude: 72.9520, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam23/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam24", camera_code: "CAM24", name: "Valsad Court Road Junction", zone: "Gujarat Range", camera_type: "PTZ", latitude: 20.6161, longitude: 72.9282, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam24/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam25", camera_code: "CAM25", name: "Kutch Bhuj Gate North", zone: "Gujarat Range", camera_type: "ANPR", latitude: 23.2419, longitude: 69.6669, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam25/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam26", camera_code: "CAM26", name: "Porbandar Nehru Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 21.6417, longitude: 69.6293, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam26/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam27", camera_code: "CAM27", name: "Amreli Highway Checkpoint", zone: "Gujarat Range", camera_type: "ANPR", latitude: 21.6032, longitude: 71.2213, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam27/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam28", camera_code: "CAM28", name: "Surendranagar Wadhwan Gate", zone: "Gujarat Range", camera_type: "FIXED", latitude: 22.7284, longitude: 71.6374, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam28/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam29", camera_code: "CAM29", name: "Gandhinagar State Highway 40", zone: "Gujarat Range", camera_type: "PTZ", latitude: 23.1793, longitude: 72.6369, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam29/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: "cam30", camera_code: "CAM30", name: "Ahmedabad Airport Road ANPR", zone: "Gujarat Range", camera_type: "ANPR", latitude: 23.0732, longitude: 72.6347, status: "ONLINE", is_active: true, stream_url: "/api/cctv/stream/cam30/index.m3u8", created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
];

export const MOCK_ALERTS: Alert[] = [
  {
    id: "alt-101",
    alert_code: "ALT-20260913-9001",
    alert_type: "ANPR_WATCHLIST_HIT",
    severity: "HIGH",
    camera_id: "cam01",
    title: "Watchlist Vehicle Sighting: GJ05CD5678",
    description: "ANPR camera detected vehicle flagged in VAHAN FIR database.",
    confidence: 0.98,
    status: "OPEN",
    evidence_url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    created_at: new Date().toISOString(),
  },
  {
    id: "alt-102",
    alert_code: "ALT-20260913-9002",
    alert_type: "WEAPON_DETECTED",
    severity: "CRITICAL",
    camera_id: "cam02",
    title: "Possible Firearm Detection",
    description: "AI Object Detection flagged weapon signature at SG Highway Gate 4.",
    confidence: 0.89,
    status: "OPEN",
    evidence_url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    created_at: new Date(Date.now() - 600000).toISOString(),
  },
];

export const MOCK_DETECTIONS: Detection[] = [
  {
    id: "det-1",
    camera_id: "cam01",
    object_type: "vehicle",
    confidence: 0.95,
    bbox: { x1: 100, y1: 120, x2: 350, y2: 400 },
    timestamp: new Date().toISOString(),
  },
  {
    id: "det-2",
    camera_id: "cam01",
    object_type: "person",
    confidence: 0.91,
    bbox: { x1: 400, y1: 150, x2: 480, y2: 380 },
    timestamp: new Date(Date.now() - 30000).toISOString(),
  },
];

export const MOCK_WATCHLISTS: Watchlist[] = [
  {
    id: "wl-1",
    name: "Stolen Vehicles (VAHAN FIR)",
    category: "VEHICLE",
    priority: "HIGH",
    description: "Active FIR stolen vehicle registry",
    active: true,
    entries_count: 142,
    created_at: new Date().toISOString(),
  },
];

export const MOCK_WATCHLIST_ENTRIES: WatchlistEntry[] = [
  {
    id: "wle-1",
    watchlist_id: "wl-1",
    reference_value: "GJ05CD5678",
    normalized_reference: "GJ05CD5678",
    category: "VEHICLE",
    priority: "HIGH",
    reason: "Stolen vehicle FIR #402/2026 Surat Police",
    active: true,
    created_at: new Date().toISOString(),
  },
];

export const MOCK_INVESTIGATIONS: Investigation[] = [
  {
    id: "inv-1",
    title: "Ring Road Suspect Movement Investigation",
    status: "IN_PROGRESS",
    assigned_officer_name: "Inspector V. K. Sharma",
    case_number: "CASE-1000284",
    created_at: new Date().toISOString(),
  },
];

export const MOCK_AUDIT_LOGS: AuditLogItem[] = [
  {
    id: "aud-1",
    event_type: "CAMERA_STREAM_ACCESSED",
    actor: "Operator-GJ01",
    resource: "cam01",
    timestamp: new Date().toISOString(),
  },
];

export interface CCTVCameraEntry {
  id: string;
  name: string;
  location?: string;
  zone?: string;
  type?: string;
  status?: string;
  latitude?: number;
  longitude?: number;
}

export interface CCTVCatalogueResponse {
  status: string;
  message?: string;
  cameras: CCTVCameraEntry[];
  totalCount?: number;
  source?: string;
}

export const cctvApi = {
  /** Fetch camera catalogue from CDN proxy (or fallback) */
  async getCatalogue(): Promise<CCTVCatalogueResponse> {
    try {
      const res = await fetch("/api/cctv/cameras");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data && Array.isArray(data.cameras) && data.cameras.length > 0) {
        return data;
      }
    } catch {
      // Ignore proxy error and fall back to local MOCK_CAMERAS
    }

    return {
      status: "FALLBACK_GUJARAT",
      cameras: MOCK_CAMERAS.map((c) => ({
        id: c.id,
        name: c.name,
        location: c.zone,
        zone: c.zone,
        type: c.camera_type,
        status: c.status.toLowerCase(),
        latitude: c.latitude,
        longitude: c.longitude,
      })),
      totalCount: MOCK_CAMERAS.length,
      source: "fallback",
    };
  },

  getStreamUrl(cameraId: string): string {
    return `/api/cctv/stream/${cameraId}/index.m3u8`;
  },
};
