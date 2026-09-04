import uuid
from datetime import datetime
from pydantic import BaseModel


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
