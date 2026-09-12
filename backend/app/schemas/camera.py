import uuid
from datetime import datetime
from pydantic import BaseModel


class CameraCreate(BaseModel):
    camera_code: str
    name: str
    description: str | None = None
    department_id: uuid.UUID | None = None
    zone: str = "General"
    camera_type: str = "PTZ"
    manufacturer: str = "Hikvision"
    model: str = "DS-2CD2043G2"
    protocol: str = "RTSP"
    rtsp_url: str | None = None
    stream_url: str | None = None
    vms_reference: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    zone: str | None = None
    camera_type: str | None = None
    protocol: str | None = None
    rtsp_url: str | None = None
    stream_url: str | None = None
    vms_reference: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str | None = None
    is_active: bool | None = None


class CameraRead(BaseModel):
    id: uuid.UUID
    camera_code: str
    name: str
    description: str | None = None
    department_id: uuid.UUID | None = None
    zone: str | None = None
    camera_type: str = "CCTV"
    manufacturer: str | None = None
    model: str | None = None
    protocol: str = "RTSP"
    stream_url: str | None = None
    vms_reference: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str = "ONLINE"
    is_active: bool = True
    last_heartbeat: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CameraStreamDescriptor(BaseModel):
    camera_id: uuid.UUID
    camera_code: str
    protocol: str
    session_url: str
    hls_url: str | None = None
    webrtc_url: str | None = None
    status: str


class CameraHealthCheckResponse(BaseModel):
    camera_id: uuid.UUID
    status: str
    latency_ms: float | None = None
    checked_at: datetime
