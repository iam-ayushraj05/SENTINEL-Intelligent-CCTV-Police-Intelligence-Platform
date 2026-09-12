import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, Float, String, ForeignKey, Text, JSON, Boolean, Integer
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class PhoneVerification(Base, TimestampMixin):
        """Manages phone number verification for alert recipients."""
        __tablename__ = "phone_verifications"

        id: Mapped[uuid.UUID] = uuid_column()
        user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
        phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
        otp: Mapped[str | None] = mapped_column(String(6), nullable=True)
        otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
        verification_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
        block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
        failed_attempts: Mapped[int] = mapped_column(default=0)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class AlertRecipient(Base, TimestampMixin):
        """Stores alert recipients and their preferences."""
        __tablename__ = "alert_recipients"

        id: Mapped[uuid.UUID] = uuid_column()
        name: Mapped[str] = mapped_column(String(200))
        designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
        department: Mapped[str | None] = mapped_column(String(100), nullable=True)
        role: Mapped[str | None] = mapped_column(String(100), nullable=True)
        phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
        phone_verification_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("phone_verifications.id", ondelete="CASCADE"), nullable=True)
        recipient_type: Mapped[str] = mapped_column(String(50), default="OPERATOR")  # OPERATOR, EMERGENCY, POLICE, HOSPITAL
        alert_preference: Mapped[str] = mapped_column(String(50), default="ALL")  # ALL, NORMAL, HIGH, EMERGENCY
        email: Mapped[str | None] = mapped_column(String(200), nullable=True)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class EmergencyIncident(Base, TimestampMixin):
        """Tracks emergency incidents detected by AI or manually triggered."""
        __tablename__ = "emergency_incidents"

        id: Mapped[uuid.UUID] = uuid_column()
        sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
        incident_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        incident_type: Mapped[str] = mapped_column(String(100), index=True)  # ACCIDENT, FIRE, CROWD_ANOMALY, etc.
        title: Mapped[str | None] = mapped_column(String(300), nullable=True)
        severity: Mapped[str] = mapped_column(String(30), index=True)  # LOW, MEDIUM, HIGH, CRITICAL
        priority: Mapped[str | None] = mapped_column(String(30), default="HIGH", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
        detection_source: Mapped[str] = mapped_column(String(50), default="AI")  # AI, MANUAL, SENSOR
        camera_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
        location_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        location_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        location_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
        description: Mapped[str] = mapped_column(Text)
        ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
        detected_objects: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # vehicles, persons, objects
        status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)  # OPEN, ACKNOWLEDGED, IN_PROGRESS, UNDER_REVIEW, RESOLVED, CLOSED
        source_alert_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
        source_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
        assigned_recipient: Mapped[str | None] = mapped_column(String(200), nullable=True)
        operator_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
        evidence_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
        created_by: Mapped[str | None] = mapped_column(String(100), default="SYSTEM")
        closed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
        closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

        @property
        def case_number(self) -> str:
            return self.incident_code

        @property
        def case_id(self) -> uuid.UUID:
            return self.id

        @property
        def event_type(self) -> str:
            return self.incident_type

        @property
        def confidence(self) -> float | None:
            return self.ai_confidence

    class IncidentTimeline(Base):
        """Chronological timeline of events for an incident/case."""
        __tablename__ = "incident_timelines"

        id: Mapped[uuid.UUID] = uuid_column()
        incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"))
        case_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
        event_type: Mapped[str] = mapped_column(String(100))  # CASE_CREATED, ALERT_RECEIVED, CASE_ACKNOWLEDGED, CASE_ASSIGNED, STATUS_CHANGED, etc.
        camera_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
        actor_id: Mapped[str | None] = mapped_column(String(100), default="SYSTEM")
        event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
        description: Mapped[str] = mapped_column(Text)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class AmbulanceDispatch(Base, TimestampMixin):
        """Tracks ambulance/emergency medical response."""
        __tablename__ = "ambulance_dispatch"

        id: Mapped[uuid.UUID] = uuid_column()
        incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"))
        ambulance_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
        ambulance_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
        hospital_name: Mapped[str] = mapped_column(String(300))
        hospital_phone: Mapped[str] = mapped_column(String(20))
        hospital_latitude: Mapped[float] = mapped_column(Float)
        hospital_longitude: Mapped[float] = mapped_column(Float)
        estimated_distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
        estimated_arrival_minutes: Mapped[int | None] = mapped_column(nullable=True)
        dispatch_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
        status: Mapped[str] = mapped_column(String(30), default="DISPATCHED", index=True)  # DISPATCHED, ENROUTE, ARRIVED, COMPLETED
        ambulance_location_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        ambulance_location_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class EmergencyCall(Base, TimestampMixin):
        """Records emergency calls and TTS messages."""
        __tablename__ = "emergency_calls"

        id: Mapped[uuid.UUID] = uuid_column()
        incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"))
        recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_recipients.id"))
        phone_number: Mapped[str] = mapped_column(String(20))
        call_type: Mapped[str] = mapped_column(String(50))  # TTS_ALERT, EMERGENCY, POLICE, HOSPITAL
        message_text: Mapped[str] = mapped_column(Text)
        status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)  # PENDING, RINGING, CONNECTED, COMPLETED, FAILED
        call_duration_seconds: Mapped[int | None] = mapped_column(nullable=True)
        external_call_id: Mapped[str | None] = mapped_column(String(200), nullable=True)  # Twilio call SID, etc.
        retry_count: Mapped[int] = mapped_column(default=0)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class AlertDelivery(Base, TimestampMixin):
        """Persists one active or completed alert for a recipient."""
        __tablename__ = "alert_deliveries"

        id: Mapped[uuid.UUID] = uuid_column()
        incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), nullable=True)
        recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_recipients.id", ondelete="CASCADE"))
        recipient_name: Mapped[str] = mapped_column(String(200))
        phone_number: Mapped[str] = mapped_column(String(20))
        risk_level: Mapped[str] = mapped_column(String(30))
        message_text: Mapped[str] = mapped_column(Text)
        status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
        is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
        recurrence_interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
        started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
        last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        next_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
        stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
        send_count: Mapped[int] = mapped_column(Integer, default=0)
        last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
        feedback_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        feedback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class AlertSendAttempt(Base, TimestampMixin):
        """Audit trail for every provider send attempt."""
        __tablename__ = "alert_send_attempts"

        id: Mapped[uuid.UUID] = uuid_column()
        alert_delivery_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_deliveries.id", ondelete="CASCADE"))
        recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_recipients.id", ondelete="CASCADE"))
        phone_number: Mapped[str] = mapped_column(String(20))
        status: Mapped[str] = mapped_column(String(30))
        provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    class NotificationLog(Base, TimestampMixin):
        """Provider audit log; secrets are never persisted."""
        __tablename__ = "notification_logs"

        id: Mapped[uuid.UUID] = uuid_column()
        alert_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
        recipient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
        channel: Mapped[str] = mapped_column(String(30), default="SMS")
        provider: Mapped[str] = mapped_column(String(50), default="twilio")
        message: Mapped[str] = mapped_column(Text)
        status: Mapped[str] = mapped_column(String(30))
        provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
        error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        attempt_count: Mapped[int] = mapped_column(Integer, default=1)
        sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    class CaseMessage(Base, TimestampMixin):
        """Stores communications, responses, comments, and replies for emergency cases."""
        __tablename__ = "case_messages"

        id: Mapped[uuid.UUID] = uuid_column()
        case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True)
        case_number: Mapped[str] = mapped_column(String(100), index=True)
        sender_id: Mapped[str] = mapped_column(String(100), default="Operator")
        sender_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
        recipient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("alert_recipients.id", ondelete="SET NULL"), nullable=True)
        message: Mapped[str] = mapped_column(Text)
        message_type: Mapped[str] = mapped_column(String(50), default="RESPONSE", index=True)  # RESPONSE, COMMENT, REPLY, SYSTEM_EVENT
        parent_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("case_messages.id", ondelete="CASCADE"), nullable=True)
        read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="SENT", index=True)  # SENT, DELIVERED, READ
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class CaseReportDocument(Base, TimestampMixin):
        """Tracks generated DOCX case reports, SHA-256 hashes, versioning, and document links."""
        __tablename__ = "case_report_documents"

        id: Mapped[uuid.UUID] = uuid_column()
        incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("emergency_incidents.id", ondelete="CASCADE"), index=True)
        case_number: Mapped[str] = mapped_column(String(100), index=True)
        document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
        document_type: Mapped[str] = mapped_column(String(50), default="CASE_REPORT", index=True)
        file_name: Mapped[str] = mapped_column(String(255))
        storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
        document_hash: Mapped[str | None] = mapped_column(String(64), index=True)  # SHA-256
        version: Mapped[int] = mapped_column(Integer, default=1)
        status: Mapped[str] = mapped_column(String(30), default="GENERATED", index=True)  # PENDING, GENERATING, GENERATED, GENERATION_FAILED, ARCHIVED
        created_by: Mapped[str | None] = mapped_column(String(100), default="SYSTEM")
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

except ImportError:
    class PhoneVerification:
        pass
    class AlertRecipient:
        pass
    class EmergencyIncident:
        pass
    class IncidentTimeline:
        pass
    class AmbulanceDispatch:
        pass
    class EmergencyCall:
        pass
    class AlertDelivery:
        pass
    class AlertSendAttempt:
        pass
    class NotificationLog:
        pass
    class CaseMessage:
        pass
    class CaseReportDocument:
        pass
