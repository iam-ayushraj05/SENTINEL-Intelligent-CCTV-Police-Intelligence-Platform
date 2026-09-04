import uuid
from datetime import datetime
from pydantic import BaseModel


class AlertCreate(BaseModel):
    alert_type: str
    severity: str
    camera_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    confidence: float | None = None
    evidence_url: str | None = None
    metadata_json: dict | None = None


class AlertUpdate(BaseModel):
    status: str | None = None  # ACKNOWLEDGED, INVESTIGATING, RESOLVED, DISMISSED
    assigned_officer: str | None = None
    description: str | None = None


class AlertRead(BaseModel):
    id: uuid.UUID
    alert_code: str
    alert_type: str
    severity: str
    camera_id: uuid.UUID | None = None
    camera_name: str | None = None
    camera_code: str | None = None
    title: str
    description: str | None = None
    confidence: float | None = None
    status: str
    assigned_officer: str | None = None
    evidence_url: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    officer_name: str | None = "Operator"
    note: str | None = None


class AlertAssignRequest(BaseModel):
    officer_name: str
