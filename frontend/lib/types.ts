export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type CameraStatus = "ONLINE" | "OFFLINE" | "DEGRADED" | "UNKNOWN";
export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "INVESTIGATING" | "RESOLVED" | "DISMISSED";
export type UserRole = "ADMIN" | "SUPERVISOR" | "OPERATOR" | "INVESTIGATOR" | "VIEWER";

export interface Camera {
  id: string;
  camera_code: string;
  name: string;
  description?: string;
  department_id?: string;
  zone?: string;
  camera_type: string;
  manufacturer?: string;
  model?: string;
  protocol: string;
  feed_type?: string;
  stream_url?: string;
  source_url?: string;
  vms_reference?: string;
  latitude?: number;
  longitude?: number;
  status: CameraStatus;
  is_active: boolean;
  fps?: number;
  resolution?: string;
  ai_detection_status?: string;
  last_detection?: string;
  alert_count?: number;
  last_heartbeat?: string;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  alert_code: string;
  alert_type: string;
  severity: Severity;
  camera_id?: string;
  camera_name?: string;
  camera_code?: string;
  title: string;
  description?: string;
  confidence?: number;
  verification_status?: string;
  investigation_status?: string;
  evidence_url?: string;
  status: AlertStatus;
  assigned_officer?: string;
  evidence_frame?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Detection {
  id: string;
  camera_id: string;
  object_type: string;
  confidence: number;
  bbox: { x: number; y: number; w: number; h: number };
  track_id?: string;
  frame_reference?: string;
  timestamp: string;
}

export interface Sighting {
  id: string;
  camera_id: string;
  camera_name?: string;
  timestamp: string;
  confidence: number;
  latitude?: number;
  longitude?: number;
  vehicle_type?: string;
  color?: string;
  evidence_url?: string;
  metadata_json?: Record<string, any>;
}

export interface VehicleIntelligence {
  plate: string;
  normalized_plate: string;
  vehicle_type?: string;
  color?: string;
  make?: string;
  model?: string;
  first_seen: string;
  last_seen: string;
  total_sightings: number;
  sightings: Sighting[];
  watchlist_matches: Array<{ id: string; priority: string; source_system: string }>;
  registered_owner?: Record<string, any>;
  metadata_json?: Record<string, any>;
  match_scores?: Record<string, number>;
  deleted?: boolean;
}

export interface InvestigationNote {
  id: string;
  investigation_id: string;
  author: string;
  note: string;
  created_at: string;
}

export interface Investigation {
  id: string;
  case_number: string;
  title: string;
  description?: string;
  status: string;
  assigned_officer_name?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  notes: InvestigationNote[];
  events: any[];
  evidence: Array<{ id: string; code: string; type: string; url: string }>;
  person_details?: Array<Record<string, any>>;
}

export interface Watchlist {
  id: string;
  name: string;
  description?: string;
  entity_type: string;
  status: string;
  created_at: string;
}

export interface WatchlistEntry {
  id: string;
  watchlist_id: string;
  subject_reference: string;
  normalized_reference: string;
  source_system?: string;
  priority: string;
  active: boolean;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  username: string;
  action: string;
  resource: string;
  result: string;
  ip_address: string;
  timestamp: string;
}

export interface DashboardSummary {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  degraded_cameras: number;
  active_alerts: number;
  critical_alerts: number;
  high_alerts: number;
  ai_events_today: number;
  persons_detected_today: number;
  vehicles_detected_today: number;
  recent_incidents_count: number;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  badge_number?: string;
  is_active: boolean;
}
