from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    degraded_cameras: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    ai_events_today: int
    persons_detected_today: int
    vehicles_detected_today: int
    recent_incidents_count: int


class SystemHealthSummary(BaseModel):
    database_status: str
    redis_status: str
    kafka_status: str
    ai_engine_status: str
    stream_gateway_status: str
    active_workers: int
    average_fps: float
    average_latency_ms: float
