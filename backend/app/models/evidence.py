import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, String, ForeignKey, Text, Float, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Evidence(Base, TimestampMixin):
        __tablename__ = "evidences"

        id: Mapped[uuid.UUID] = uuid_column()
        file_name: Mapped[str] = mapped_column(String(250))
        file_path: Mapped[str] = mapped_column(String(500))
        mime_type: Mapped[str] = mapped_column(String(100), default="image/jpeg")
        file_hash: Mapped[str | None] = mapped_column(String(100), nullable=True)
        investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id"), nullable=True)
        evidence_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        evidence_type: Mapped[str] = mapped_column(String(50), default="DIGITAL")
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        status: Mapped[str] = mapped_column(String(40), default="IN_CUSTODY", index=True)
        current_location: Mapped[str | None] = mapped_column(String(250), nullable=True)
        current_custodian: Mapped[str | None] = mapped_column(String(150), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class CustodyEvent(Base):
        __tablename__ = "evidence_custody_events"

        id: Mapped[uuid.UUID] = uuid_column()
        evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="CASCADE"), index=True)
        from_person: Mapped[str | None] = mapped_column(String(150), nullable=True)
        from_location: Mapped[str | None] = mapped_column(String(250), nullable=True)
        to_person: Mapped[str | None] = mapped_column(String(150), nullable=True)
        to_location: Mapped[str | None] = mapped_column(String(250), nullable=True)
        reason: Mapped[str] = mapped_column(Text)
        condition_before: Mapped[str | None] = mapped_column(Text, nullable=True)
        condition_after: Mapped[str | None] = mapped_column(Text, nullable=True)
        seal_condition: Mapped[str | None] = mapped_column(String(150), nullable=True)
        acknowledgement: Mapped[str | None] = mapped_column(String(250), nullable=True)
        created_by: Mapped[str] = mapped_column(String(100))
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

except ImportError:
    class Evidence: pass
    class CustodyEvent: pass
