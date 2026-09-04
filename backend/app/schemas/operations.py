import uuid
from datetime import datetime
from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    name: str
    description: str | None = None
    entity_type: str  # VEHICLE, PERSON_REFERENCE, OBJECT


class WatchlistRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    entity_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistEntryCreate(BaseModel):
    subject_reference: str
    source_system: str | None = "MANUAL"
    priority: str = "HIGH"
    metadata_json: dict | None = None


class WatchlistEntryRead(BaseModel):
    id: uuid.UUID
    watchlist_id: uuid.UUID
    subject_reference: str
    normalized_reference: str
    source_system: str | None = None
    priority: str
    metadata_json: dict | None = None
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InvestigationCreate(BaseModel):
    title: str
    description: str | None = None
    assigned_officer_name: str | None = None


class InvestigationNoteCreate(BaseModel):
    note: str
    author: str | None = None


class InvestigationNoteRead(BaseModel):
    id: uuid.UUID
    investigation_id: uuid.UUID
    author: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvestigationRead(BaseModel):
    id: uuid.UUID
    case_number: str
    title: str
    description: str | None = None
    status: str
    assigned_officer_name: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    notes: list[InvestigationNoteRead] = []
    events: list[dict] = []
    evidence: list[dict] = []

    class Config:
        from_attributes = True
