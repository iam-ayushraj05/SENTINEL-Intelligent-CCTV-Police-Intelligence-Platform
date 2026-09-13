import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PhoneVerificationRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to verify")


class PhoneVerificationOTP(BaseModel):
    phone_number: str
    otp: str


class PhoneVerificationRead(BaseModel):
    id: uuid.UUID
    phone_number: str
    is_verified: bool
    is_blocked: bool
    verification_timestamp: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRecipientCreate(BaseModel):
    name: str
    designation: str | None = None
    department: str | None = None
    role: str | None = "OPERATOR"
    phone_verification_id: uuid.UUID | None = None
    phone_number: str | None = Field(None, min_length=8, max_length=20)
    recipient_type: str = "OPERATOR"
    alert_preference: str = "ALL"
    email: str | None = None
    is_active: bool = True


class RecipientAlertRequest(BaseModel):
    recipient_ids: list[uuid.UUID] = Field(..., min_length=1, description="Saved recipients to notify")
    risk_level: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH)$")
    message: str = Field(..., min_length=1, max_length=1000)
    feedback_message: str | None = Field(None, max_length=2000)
    incident_id: uuid.UUID | None = None
    location_latitude: float | None = Field(None, ge=-90, le=90)
    location_longitude: float | None = Field(None, ge=-180, le=180)


class SmsTestRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=1000)


class RecipientAlertResponse(BaseModel):
    status: str
    risk_level: str
    recipient_ids: list[uuid.UUID]
    recipients_count: int
    sms_status: str
    recipient_name: str
    phone_number: str
    provider_message_ids: list[str] = Field(default_factory=list)
    send_status: str
    next_send_at: datetime | None = None
    alert_ids: list[uuid.UUID] = Field(default_factory=list)
    reason: str | None = None
    message: str


class AlertFeedbackRequest(BaseModel):
    feedback_message: str = Field(..., min_length=1, max_length=2000)


class AlertDeliveryRead(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID | None
    recipient_id: uuid.UUID
    recipient_name: str
    phone_number: str
    risk_level: str
    message_text: str
    status: str
    is_recurring: bool
    recurrence_interval_seconds: int
    started_at: datetime
    last_sent_at: datetime | None
    next_send_at: datetime | None
    stopped_at: datetime | None
    provider_message_id: str | None
    send_count: int
    last_error: str | None
    feedback_message: str | None
    feedback_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRecipientUpdate(BaseModel):
    name: str | None = None
    designation: str | None = None
    department: str | None = None
    role: str | None = None
    phone_number: str | None = None
    alert_preference: str | None = None
    email: str | None = None
    is_active: bool | None = None


class AlertRecipientRead(BaseModel):
    id: uuid.UUID
    name: str
    designation: str | None = None
    department: str | None = None
    role: str | None = None
    phone_verification_id: uuid.UUID | None = None
    phone_number: str | None = None
    recipient_type: str = "OPERATOR"
    alert_preference: str = "ALL"
    email: str | None = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class EmergencyIncidentCreate(BaseModel):
    incident_type: str
    severity: str
    detection_source: str
    camera_id: uuid.UUID | None = None
    location_latitude: float | None = None
    location_longitude: float | None = None
    location_name: str | None = None
    description: str
    ai_confidence: float | None = None
    detected_objects: dict | None = None
    operator_comments: str | None = None


class EmergencyIncidentUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    operator_comments: str | None = None
    severity: str | None = None
    assigned_recipient: str | None = None


class EmergencyIncidentRead(BaseModel):
    id: uuid.UUID
    incident_code: str
    case_number: str | None = None
    sequence_number: int | None = None
    title: str | None = None
    incident_type: str
    severity: str
    priority: str | None = "HIGH"
    detection_source: str
    camera_id: uuid.UUID | str | None = None
    location_latitude: float | None
    location_longitude: float | None
    location_name: str | None
    description: str
    ai_confidence: float | None
    detected_objects: dict | None
    status: str
    source_alert_id: uuid.UUID | None = None
    source_event_id: str | None = None
    assigned_recipient: str | None = None
    operator_comments: str | None
    created_by: str | None = "SYSTEM"
    closed_by: str | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentTimelineRead(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    case_number: str | None = None
    event_type: str
    camera_id: uuid.UUID | str | None = None
    actor_id: str | None = "SYSTEM"
    event_time: datetime | None = None
    description: str
    message: str | None = None
    metadata_json: dict | None = None

    class Config:
        from_attributes = True


class AmbulanceDispatchCreate(BaseModel):
    hospital_name: str
    hospital_phone: str
    hospital_latitude: float
    hospital_longitude: float
    ambulance_id: str | None = None
    ambulance_name: str | None = None


class AmbulanceDispatchRead(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    ambulance_id: str | None
    ambulance_name: str | None
    hospital_name: str
    hospital_phone: str
    hospital_latitude: float
    hospital_longitude: float
    estimated_distance_km: float | None
    estimated_arrival_minutes: int | None
    status: str
    ambulance_location_latitude: float | None
    ambulance_location_longitude: float | None
    dispatch_time: datetime

    class Config:
        from_attributes = True


class EmergencyCallRead(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    phone_number: str
    call_type: str
    message_text: str
    status: str
    call_duration_seconds: int | None
    retry_count: int
    error_message: str | None
    started_at: datetime | None
    ended_at: datetime | None

    class Config:
        from_attributes = True


class CustomAlertMessage(BaseModel):
    message: str = Field(..., description="Custom message to be converted to speech")


class IncidentCorrelationData(BaseModel):
    camera_id: uuid.UUID
    event_type: str
    timestamp: datetime
    confidence: float | None = None
    metadata: dict | None = None


class CaseMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    message_type: str = "RESPONSE"  # RESPONSE, COMMENT, REPLY, SYSTEM_EVENT
    recipient_id: uuid.UUID | None = None
    parent_message_id: uuid.UUID | None = None
    sender_id: str | None = "Operator"
    sender_name: str | None = None


class CaseMessageRead(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    sender_id: str
    sender_name: str | None = None
    recipient_id: uuid.UUID | None = None
    message: str
    message_type: str
    parent_message_id: uuid.UUID | None = None
    read_at: datetime | None = None
    status: str = "SENT"
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class CaseCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)
    sender_id: str | None = "Operator"


class CaseReplyCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    sender_id: str | None = "Operator"


class CaseClosureRequest(BaseModel):
    operator_comments: str | None = None
    closure_reason: str | None = "CASE_RESOLVED"


class CaseReportDocumentRead(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    case_number: str
    document_id: uuid.UUID | None = None
    document_type: str = "CASE_REPORT"
    file_name: str
    storage_key: str | None = None
    document_hash: str | None = None
    version: int = 1
    status: str = "GENERATED"
    created_by: str | None = "SYSTEM"
    created_at: datetime
    updated_at: datetime | None = None
    download_url: str | None = None
    view_url: str | None = None

    class Config:
        from_attributes = True

