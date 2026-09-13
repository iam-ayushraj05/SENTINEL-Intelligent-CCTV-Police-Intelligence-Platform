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
    if (typeof window !== "undefined") sessionStorage.setItem("sentinel_access_token", result.access_token);
    return result;
  },
  logout: async () => {
    try { await fetcher<void>("/auth/logout", { method: "POST" }); } catch { /* local session cleanup still runs */ }
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("sentinel_access_token");
      sessionStorage.clear();
    }
    return { success: true };
  },
  getUsers: () => fetcher<User[]>("/auth/users").catch(() => []),

  // Dashboard
  getDashboardSummary: () =>
    fetcher<DashboardSummary>("/dashboard/summary").catch(() => ({
      total_cameras: 6,
      online_cameras: 5,
      offline_cameras: 0,
      degraded_cameras: 1,
      active_alerts: 3,
      critical_alerts: 1,
      high_alerts: 2,
      ai_events_today: 1420,
      persons_detected_today: 850,
      vehicles_detected_today: 570,
      recent_incidents_count: 2,
    })),
  getDashboardActivity: () =>
    fetcher<any>("/dashboard/activity").catch(() => ({
      recent_alerts: [],
      health: {
        database_status: "HEALTHY (PostgreSQL+PostGIS)",
        redis_status: "HEALTHY (Cache)",
        kafka_status: "HEALTHY (Event Bus)",
        ai_engine_status: "RUNNING (YOLOv8 & ANPR)",
        stream_gateway_status: "ACTIVE (MediaMTX)",
        active_workers: 4,
        average_fps: 28.5,
        average_latency_ms: 38.2,
      },
    })),

  // Cameras
  getCameras: (status?: string, zone?: string) => {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (zone) params.append("zone", zone);
    const q = params.toString() ? `?${params.toString()}` : "";
    return fetcher<Camera[]>(`/cameras${q}`).catch(() => MOCK_CAMERAS);
  },
  getCamera: (id: string) => fetcher<Camera>(`/cameras/${id}`).catch(() => MOCK_CAMERAS[0]),
  createCamera: (data: Partial<Camera>) =>
    fetcher<Camera>("/cameras", { method: "POST", body: JSON.stringify(data) }),
  getCameraStream: (id: string) =>
    fetcher<any>(`/cameras/${id}/stream`).catch(() => ({
      camera_id: id,
      protocol: "WEBRTC",
      session_url: "http://localhost:8889/live/stream",
      status: "STREAMING",
    })),

  // Alerts
  getAlerts: (severity?: string, status?: string) => {
    const params = new URLSearchParams();
    if (severity) params.append("severity", severity);
    if (status) params.append("status", status);
    const q = params.toString() ? `?${params.toString()}` : "";
    return fetcher<Alert[]>(`/alerts${q}`).catch(() => MOCK_ALERTS);
  },
  getAlert: (id: string) => fetcher<Alert>(`/alerts/${id}`).catch(() => MOCK_ALERTS[0]),
  createAlert: (data: {
    alert_type: string;
    severity: string;
    title: string;
    description?: string;
    camera_id?: string;
  }) => fetcher<Alert>("/alerts", { method: "POST", body: JSON.stringify({ ...data, metadata_json: { source: "MANUAL" } }) }),
  acknowledgeAlert: (id: string, officer_name?: string, note?: string) =>
    fetcher<Alert>(`/alerts/${id}/acknowledge`, {
      method: "POST",
      body: JSON.stringify({ officer_name, note }),
    }),
  assignAlert: (id: string, officer_name: string) =>
    fetcher<Alert>(`/alerts/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ officer_name }),
    }),
  resolveAlert: (id: string) => fetcher<Alert>(`/alerts/${id}/resolve`, { method: "POST" }),
  dismissAlert: (id: string) => fetcher<Alert>(`/alerts/${id}/dismiss`, { method: "POST" }),
  stopAlertEscalation: (id: string) => fetcher<{ status: string }>(`/alerts/${id}/stop-escalation`, { method: "POST" }),

  // Detections & Vehicles
  getDetections: () => fetcher<Detection[]>("/detections").catch(() => []),
  getVehicleIntelligence: (plate: string, fromTime?: string, toTime?: string) =>
    fetcher<VehicleIntelligence>(`/vehicles/${plate}/sightings${fromTime || toTime ? `?${new URLSearchParams({ ...(fromTime ? { from_time: fromTime } : {}), ...(toTime ? { to_time: toTime } : {}) }).toString()}` : ""}`).catch(() => ({
      plate,
      normalized_plate: plate.replace(/[^A-Z0-9]/gi, "").toUpperCase(),
      vehicle_type: "Mahindra Bolero - Silver",
      color: "Silver",
      make: "Mahindra",
      model: "Bolero",
      first_seen: new Date(Date.now() - 3600000 * 5).toISOString(),
      last_seen: new Date().toISOString(),
      total_sightings: 4,
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

// Fallback Mock Data for immediate offline rendering
export const MOCK_CAMERAS: Camera[] = [
  {
    id: "cam-1",
    camera_code: "CAM-GJ01-001",
    name: "16 Fake Security Cameras Prank",
    description: "Local video feed assigned to Ahmedabad Ring Road North Junction",
    zone: "Ahmedabad Central",
    camera_type: "ANPR",
    manufacturer: "Hikvision Sentinel",
    model: "DS-2CD2043G2-I",
    protocol: "FILE",
    stream_url: "http://localhost:8000/api/v1/feeds/local-camera-video",
    vms_reference: "VMS-GJ-1024",
    latitude: 23.0225,
    longitude: 72.5714,
    status: "ONLINE",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cam-2",
    camera_code: "CAM-GJ01-002",
    name: "SG Highway Express Gate 4",
    description: "PTZ Dome camera monitoring SG Highway Gate 4 traffic",
    zone: "Ahmedabad West",
    camera_type: "PTZ",
    manufacturer: "Hikvision Sentinel",
    model: "DS-2CD2043G2-I",
    protocol: "RTSP",
    stream_url: "http://localhost:8889/live/cam02",
    vms_reference: "VMS-GJ-1025",
    latitude: 23.09,
    longitude: 72.5342,
    status: "ONLINE",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cam-3",
    camera_code: "CAM-GJ01-003",
    name: "Kalupur Station Entrance",
    description: "Fixed broad-angle camera at Kalupur Railway Terminal Entrance",
    zone: "Ahmedabad East",
    camera_type: "FIXED",
    manufacturer: "Dahua Sentinel",
    model: "DH-IPC-HFW",
    protocol: "RTSP",
    stream_url: "http://localhost:8889/live/cam03",
    vms_reference: "VMS-GJ-1026",
    latitude: 23.027,
    longitude: 72.6012,
    status: "ONLINE",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cam-4",
    camera_code: "CAM-GJ05-001",
    name: "Majura Gate Circle",
    description: "ANPR High-speed camera at Surat Majura Gate Roundabout",
    zone: "Surat South",
    camera_type: "ANPR",
    manufacturer: "Axis Communications",
    model: "Q1786-LE",
    protocol: "RTSP",
    stream_url: "http://localhost:8889/live/cam04",
    vms_reference: "VMS-GJ-1027",
    latitude: 21.1702,
    longitude: 72.8311,
    status: "ONLINE",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cam-5",
    camera_code: "CAM-GJ18-001",
    name: "Sector 11 Secretariat Plaza",
    description: "Government Complex Entrance PTZ Camera",
    zone: "Gandhinagar Govt Complex",
    camera_type: "PTZ",
    manufacturer: "Hikvision Sentinel",
    model: "DS-2CD2043G2-I",
    protocol: "RTSP",
    stream_url: "http://localhost:8889/live/cam05",
    vms_reference: "VMS-GJ-1028",
    latitude: 23.2156,
    longitude: 72.6369,
    status: "ONLINE",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: "cam-6",
    camera_code: "CAM-GJ03-001",
    name: "Trikon Baug Junction",
    description: "Rajkot Center Junction monitoring camera",
    zone: "Rajkot Center",
    camera_type: "FIXED",
    manufacturer: "Bosch Security",
    model: "DINION IP 7000",
    protocol: "RTSP",
    stream_url: "http://localhost:8889/live/cam06",
    vms_reference: "VMS-GJ-1029",
    latitude: 22.3039,
    longitude: 70.8022,
    status: "DEGRADED",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const MOCK_ALERTS: Alert[] = [
  {
    id: "alt-1",
    alert_code: "ALT-20260904-9981",
    alert_type: "WATCHLIST_MATCH",
    severity: "CRITICAL",
    camera_id: "cam-1",
    camera_name: "Ring Road Junction North",
    camera_code: "CAM-GJ01-001",
    title: "WATCHLIST MATCH: Stolen Vehicle GJ05CD5678",
    description: "Sighting of flagged vehicle GJ05CD5678 on camera CAM-GJ01-001. Matched against Stolen Vehicles watchlist (FIR-2026-SURAT-00412).",
    confidence: 0.96,
    status: "OPEN",
    evidence_url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
    created_at: new Date(Date.now() - 120000).toISOString(),
    updated_at: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: "alt-2",
    alert_code: "ALT-20260904-8812",
    alert_type: "CROWD_ANOMALY",
    severity: "HIGH",
    camera_id: "cam-3",
    camera_name: "Kalupur Station Entrance",
    camera_code: "CAM-GJ01-003",
    title: "ANOMALY: Sudden Crowd Concentration",
    description: "Unusual crowd assembly detected near Kalupur Station Entrance gate. Density exceeds normal threshold by 240%.",
    confidence: 0.88,
    status: "OPEN",
    evidence_url: "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=800&q=80",
    created_at: new Date(Date.now() - 900000).toISOString(),
    updated_at: new Date(Date.now() - 900000).toISOString(),
  },
  {
    id: "alt-3",
    alert_code: "ALT-20260904-7743",
    alert_type: "LOITERING",
    severity: "MEDIUM",
    camera_id: "cam-5",
    camera_name: "Sector 11 Secretariat Plaza",
    camera_code: "CAM-GJ18-001",
    title: "LOITERING: Person detected > 15 mins",
    description: "Anonymous track ID TRK-419 loitering near restricted perimeter line for over 15 minutes.",
    confidence: 0.82,
    status: "ACKNOWLEDGED",
    assigned_officer: "Sub-Inspector Rajesh Patel",
    evidence_url: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 1800000).toISOString(),
  },
];

export const MOCK_WATCHLISTS: Watchlist[] = [
  {
    id: "wl-1",
    name: "Stolen & Crime-Linked Vehicles",
    description: "Authorized statewide database of reported stolen and wanted vehicles",
    entity_type: "VEHICLE",
    status: "ACTIVE",
    created_at: new Date().toISOString(),
  },
  {
    id: "wl-2",
    name: "Persons of Interest (Authorized Watchlist)",
    description: "Controlled authorized reference watchlist for security perimeter monitoring",
    entity_type: "PERSON_REFERENCE",
    status: "ACTIVE",
    created_at: new Date().toISOString(),
  },
];

export const MOCK_WATCHLIST_ENTRIES: WatchlistEntry[] = [
  {
    id: "wle-1",
    watchlist_id: "wl-1",
    subject_reference: "GJ05CD5678",
    normalized_reference: "GJ05CD5678",
    source_system: "VAHAN_POLICE_FIR",
    priority: "HIGH",
    active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: "wle-2",
    watchlist_id: "wl-1",
    subject_reference: "GJ01XY9999",
    normalized_reference: "GJ01XY9999",
    source_system: "CRIME_BRANCH",
    priority: "CRITICAL",
    active: true,
    created_at: new Date().toISOString(),
  },
];

export const MOCK_INVESTIGATIONS: Investigation[] = [
  {
    id: "inv-1",
    case_number: "CASE-2026-GJ-0091",
    title: "Stolen Bolero Ring Road Sighting Case",
    description: "Cross-referencing CCTV sightings of GJ05CD5678 across Ring Road and SG Highway cameras.",
    status: "INVESTIGATING",
    assigned_officer_name: "Sub-Inspector Rajesh Patel",
    created_by: "admin",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date().toISOString(),
    notes: [
      {
        id: "n-1",
        investigation_id: "inv-1",
        author: "Sub-Inspector Rajesh Patel",
        note: "Verified CCTV frame from CAM-GJ01-001. Vehicle confirmed silver Mahindra Bolero heading south towards SG Highway.",
        created_at: new Date(Date.now() - 43200000).toISOString(),
      },
    ],
    events: [],
    evidence: [
      {
        id: "ev-1",
        code: "EVD-FRAME-001",
        type: "FRAME_SNAPSHOT",
        url: "https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=800&q=80",
      },
    ],
  },
];

export const MOCK_AUDIT_LOGS: AuditLogItem[] = [
  {
    id: "aud-1",
    username: "admin",
    action: "SYSTEM_INIT",
    resource: "DATABASE",
    result: "SUCCESS",
    ip_address: "127.0.0.1",
    timestamp: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: "aud-2",
    username: "operator01",
    action: "ALERT_ACKNOWLEDGE",
    resource: "Alert:ALT-20260904-7743",
    result: "SUCCESS",
    ip_address: "192.168.1.45",
    timestamp: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: "aud-3",
    username: "operator01",
    action: "GOV_DB_QUERY_VEHICLE",
    resource: "VAHAN:GJ05CD5678",
    result: "SUCCESS",
    ip_address: "192.168.1.45",
    timestamp: new Date(Date.now() - 1200000).toISOString(),
  },
];


// ==========================================
// CCTV CDN Catalogue & Stream API
// ==========================================

export interface CCTVCameraEntry {
  id: string;
  name?: string;
  location?: string;
  status?: string;
  [key: string]: unknown;
}

export interface CCTVCatalogueResponse {
  status: string;
  cameras: CCTVCameraEntry[];
  totalCount?: number;
  source?: string;
  message?: string;
}

export interface PlateSearchResult {
  id: string;
  plate_text: string;
  normalized_plate: string;
  confidence: number;
  camera_id: string;
  camera_code: string | null;
  camera_name: string | null;
  camera_zone: string | null;
  timestamp: string;
  vehicle_class: string | null;
  direction: string | null;
  snapshot_url: string | null;
}

export interface VehicleJourneyObservation {
  sequence_index: number;
  camera_id: string;
  camera_code: string | null;
  camera_name: string | null;
  zone: string | null;
  timestamp: string;
  plate_text: string;
  confidence: number;
  time_gap_seconds: number | null;
  previous_camera: string | null;
  next_camera: string | null;
  time_to_next_seconds: number | null;
}

export const cctvApi = {
  /** Fetch camera catalogue from CDN proxy (or fallback) */
  async getCatalogue(): Promise<CCTVCatalogueResponse> {
    try {
      const res = await fetch("/api/cctv/cameras");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (error) {
      console.warn("CCTV catalogue fetch failed, using backend fallback");
      // Fallback to local backend
      try {
        const cameras = await api.getCameras();
        return {
          status: "BACKEND_FALLBACK",
          cameras: cameras.map((c) => ({
            id: c.camera_code || c.id,
            name: c.name,
            location: c.zone || undefined,
            status: c.status?.toLowerCase(),
          })),
          totalCount: cameras.length,
          source: "backend",
        };
      } catch {
        return { status: "ERROR", cameras: [], totalCount: 0, source: "none" };
      }
    }
  },

  /** Get the proxied HLS stream URL for a camera */
  getStreamUrl(cameraId: string): string {
    return `/api/cctv/stream/${cameraId}/index.m3u8`;
  },

  /** Search ANPR plate observations */
  async searchPlates(params: {
    plate: string;
    camera_id?: string;
    start_time?: string;
    end_time?: string;
    min_confidence?: number;
  }): Promise<{ results: PlateSearchResult[]; total: number }> {
    const searchParams = new URLSearchParams({ plate: params.plate });
    if (params.camera_id) searchParams.set("camera_id", params.camera_id);
    if (params.start_time) searchParams.set("start_time", params.start_time);
    if (params.end_time) searchParams.set("end_time", params.end_time);
    if (params.min_confidence !== undefined) searchParams.set("min_confidence", String(params.min_confidence));
    return fetcher(`/search/plates?${searchParams}`);
  },

  /** Get cross-camera vehicle journey */
  async getVehicleJourney(plate: string, minConfidence = 0.5): Promise<{
    plate: string;
    journey_type: string;
    observation_count: number;
    observations: VehicleJourneyObservation[];
    disclaimer: string;
  }> {
    return fetcher(`/vehicles/${encodeURIComponent(plate)}/journey?min_confidence=${minConfidence}`);
  },
};
