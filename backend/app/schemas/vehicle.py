import uuid
from datetime import datetime
from pydantic import BaseModel


class SightingRead(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    camera_name: str | None = None
    timestamp: datetime
    confidence: float
    latitude: float | None = None
    longitude: float | None = None
    vehicle_type: str | None = None
    color: str | None = None
    evidence_url: str | None = None
    metadata_json: dict | None = None

    class Config:
        from_attributes = True


class VehicleIntelligenceResponse(BaseModel):
    plate: str
    normalized_plate: str
    vehicle_type: str | None = None
    color: str | None = None
    make: str | None = None
    model: str | None = None
    first_seen: datetime
    last_seen: datetime
    total_sightings: int
    sightings: list[SightingRead]
    watchlist_matches: list[dict] = []
    registered_owner: dict | None = None
    metadata_json: dict | None = None
    match_scores: dict | None = None
    deleted: bool = False


class RouteSegment(BaseModel):
    from_camera: str
    to_camera: str
    start_time: datetime
    end_time: datetime
    confidence: float
    geometry: dict | None = None


class VehicleRouteResponse(BaseModel):
    plate: str
    segments: list[RouteSegment]
