import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    PERSON_DETECTED = "PERSON_DETECTED"
    VEHICLE_DETECTED = "VEHICLE_DETECTED"
    ANPR_DETECTED = "ANPR_DETECTED"
    FACE_DETECTED = "FACE_DETECTED"
    FACE_MATCH = "FACE_MATCH"
    WEAPON_DETECTED = "WEAPON_DETECTED"
    FIRE_DETECTED = "FIRE_DETECTED"
    SMOKE_DETECTED = "SMOKE_DETECTED"
    HUMAN_ACTIVITY_DETECTED = "HUMAN_ACTIVITY_DETECTED"


class SentinelAIEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    camera_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    track_id: Optional[str] = None
    class_name: str
    confidence: float
    bounding_box: Optional[List[float]] = None
    model_name: str
    model_version: str = "1.0.0"
    source: str = "sentinel_ai_engine"
    status: str = "CONFIRMED"
    requires_human_review: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        return data
