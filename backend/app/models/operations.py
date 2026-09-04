import uuid
from datetime import datetime

try:
    from sqlalchemy import Boolean, DateTime, String, ForeignKey, Text, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Department(Base, TimestampMixin):
        __tablename__ = "departments"

        id: Mapped[uuid.UUID] = uuid_column()
        code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        name: Mapped[str] = mapped_column(String(150))
        district: Mapped[str] = mapped_column(String(100), default="Ahmedabad")
        state: Mapped[str] = mapped_column(String(100), default="Gujarat")

    class Watchlist(Base, TimestampMixin):
        __tablename__ = "watchlists"

        id: Mapped[uuid.UUID] = uuid_column()
        name: Mapped[str] = mapped_column(String(150), unique=True)
        entity_type: Mapped[str] = mapped_column(String(50))
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="ACTIVE")

    class WatchlistEntry(Base, TimestampMixin):
        __tablename__ = "watchlist_entries"

        id: Mapped[uuid.UUID] = uuid_column()
        watchlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("watchlists.id", ondelete="CASCADE"))
        subject_reference: Mapped[str] = mapped_column(String(100), index=True)
        normalized_reference: Mapped[str] = mapped_column(String(100), index=True)
        priority: Mapped[str] = mapped_column(String(30), default="HIGH")
        source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
        active: Mapped[bool] = mapped_column(Boolean, default=True)

    class Investigation(Base, TimestampMixin):
        __tablename__ = "investigations"

        id: Mapped[uuid.UUID] = uuid_column()
        case_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        title: Mapped[str] = mapped_column(String(200))
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        assigned_officer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)

    class InvestigationEvent(Base):
        __tablename__ = "investigation_events"

        id: Mapped[uuid.UUID] = uuid_column()
        investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"))
        event_type: Mapped[str] = mapped_column(String(100))
        description: Mapped[str] = mapped_column(Text)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    class InvestigationNote(Base):
        __tablename__ = "investigation_notes"

        id: Mapped[uuid.UUID] = uuid_column()
        investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"))
        author: Mapped[str] = mapped_column(String(100))
        note: Mapped[str] = mapped_column(Text)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

except ImportError:
    class Department: pass
    class Watchlist:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class WatchlistEntry:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class Investigation:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class InvestigationEvent: pass
    class InvestigationNote:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
