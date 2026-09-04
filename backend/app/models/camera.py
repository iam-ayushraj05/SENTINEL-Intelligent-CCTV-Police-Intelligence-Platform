import uuid
from datetime import datetime

try:
    from sqlalchemy import Boolean, Float, String, DateTime, ForeignKey, Text, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Camera(Base, TimestampMixin):
        __tablename__ = "cameras"

        id: Mapped[uuid.UUID] = uuid_column()
        camera_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        name: Mapped[str] = mapped_column(String(200))
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
        zone: Mapped[str | None] = mapped_column(String(100), default="General", index=True)
        camera_type: Mapped[str] = mapped_column(String(50), default="PTZ")
        manufacturer: Mapped[str | None] = mapped_column(String(100), default="Hikvision")
        model: Mapped[str | None] = mapped_column(String(100), default="DS-2CD2043G2")
        protocol: Mapped[str] = mapped_column(String(30), default="RTSP")
        rtsp_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
        stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
        vms_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
        latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="ONLINE", index=True)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class CameraSource(Base):
        __tablename__ = "camera_sources"

        id: Mapped[uuid.UUID] = uuid_column()
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"))
        vms_vendor: Mapped[str] = mapped_column(String(100), default="MockVMS")
        stream_profile: Mapped[str] = mapped_column(String(50), default="main")
        resolution: Mapped[str] = mapped_column(String(30), default="1080p")
        fps: Mapped[int] = mapped_column(default=25)

    class CameraHealthEvent(Base):
        __tablename__ = "camera_health_events"

        id: Mapped[uuid.UUID] = uuid_column()
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"))
        status: Mapped[str] = mapped_column(String(30))
        latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

except ImportError:
    class Camera:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class CameraSource:
        pass
    class CameraHealthEvent:
        pass
