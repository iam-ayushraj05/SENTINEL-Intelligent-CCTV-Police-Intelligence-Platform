import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, Float, String, ForeignKey, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, uuid_column

    class Detection(Base):
        __tablename__ = "detections"

        id: Mapped[uuid.UUID] = uuid_column()
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), index=True)
        object_class: Mapped[str] = mapped_column(String(50), index=True)
        confidence: Mapped[float] = mapped_column(Float)
        bbox: Mapped[dict] = mapped_column(JSON)
        track_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    class DetectionTrack(Base):
        __tablename__ = "detection_tracks"

        id: Mapped[uuid.UUID] = uuid_column()
        track_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        object_class: Mapped[str] = mapped_column(String(50))
        start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    class DetectionEvent(Base):
        __tablename__ = "detection_events"

        id: Mapped[uuid.UUID] = uuid_column()
        event_type: Mapped[str] = mapped_column(String(100))
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"))
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

except ImportError:
    class Detection:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class DetectionTrack:
        pass
    class DetectionEvent:
        pass
