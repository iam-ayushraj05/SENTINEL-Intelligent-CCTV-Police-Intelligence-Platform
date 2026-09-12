import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class DetectionCreate(BaseModel):
    camera_id: uuid.UUID
    object_type: str
    confidence: float
    bbox: dict
    track_id: str | None = None
    frame_reference: str | None = None
    metadata_json: dict | None = None


class DetectionRead(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    object_type: str
    confidence: float
    bbox: dict
    track_id: str | None = None
    frame_reference: str | None = None
    metadata_json: dict | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


class DetectionEventIngest(BaseModel):
    camera_id: uuid.UUID | str
    event_type: str
    confidence: float
    subject_reference: str | None = None
    evidence_url: str | None = None
    metadata_json: dict | None = None


class DetectionBatchIngest(BaseModel):
    camera_id: uuid.UUID | str
    detections: list[dict] = Field(default_factory=list)
    events: list[DetectionEventIngest] = Field(default_factory=list)
