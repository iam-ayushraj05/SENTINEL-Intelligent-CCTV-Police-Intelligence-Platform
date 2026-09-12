import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, Float, String, ForeignKey, Text, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Alert(Base, TimestampMixin):
        __tablename__ = "alerts"

        id: Mapped[uuid.UUID] = uuid_column()
        alert_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        alert_type: Mapped[str] = mapped_column(String(100))
        severity: Mapped[str] = mapped_column(String(30), index=True)
        camera_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
        title: Mapped[str] = mapped_column(String(300))
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
        event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
        verification_status: Mapped[str] = mapped_column(String(50), default="REQUIRES_VERIFICATION")
        investigation_status: Mapped[str] = mapped_column(String(50), default="PENDING")
        video_timestamp: Mapped[str | None] = mapped_column(String(100), nullable=True)
        evidence_frame: Mapped[str | None] = mapped_column(String(500), nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)
        assigned_officer: Mapped[str | None] = mapped_column(String(100), nullable=True)
        evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class AlertEvent(Base):
        __tablename__ = "alert_events"

        id: Mapped[uuid.UUID] = uuid_column()
        alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"))
        action: Mapped[str] = mapped_column(String(50))
        actor: Mapped[str] = mapped_column(String(100))
        comment: Mapped[str | None] = mapped_column(Text, nullable=True)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    class AlertAssignment(Base):
        __tablename__ = "alert_assignments"

        id: Mapped[uuid.UUID] = uuid_column()
        alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"))
        user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
        assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

except ImportError:
    class Alert:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class AlertEvent:
        pass
    class AlertAssignment:
        pass
