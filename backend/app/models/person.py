import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, Float, String, ForeignKey, Text, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Person(Base, TimestampMixin):
        __tablename__ = "persons"

        id: Mapped[uuid.UUID] = uuid_column()
        person_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
        alias: Mapped[str | None] = mapped_column(String(150), nullable=True)
        date_of_birth: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        gender: Mapped[str | None] = mapped_column(String(30), nullable=True)
        phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
        address: Mapped[str | None] = mapped_column(String(500), nullable=True)
        case_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
        case_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
        case_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
        assigned_officer: Mapped[str | None] = mapped_column(String(100), nullable=True)
        agency_unit: Mapped[str | None] = mapped_column(String(150), nullable=True)
        notes: Mapped[str | None] = mapped_column(Text, nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class PersonObservation(Base):
        __tablename__ = "person_observations"

        id: Mapped[uuid.UUID] = uuid_column()
        person_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), index=True)
        confidence: Mapped[float] = mapped_column(Float)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    class PersonMatch(Base):
        __tablename__ = "person_matches"

        id: Mapped[uuid.UUID] = uuid_column()
        person_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("persons.id"))
        similarity_score: Mapped[float] = mapped_column(Float)
        matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

except ImportError:
    class Person: pass
    class PersonObservation: pass
    class PersonMatch: pass
