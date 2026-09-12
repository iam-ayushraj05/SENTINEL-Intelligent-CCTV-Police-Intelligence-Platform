import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, Float, String, ForeignKey, JSON
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class Vehicle(Base, TimestampMixin):
        __tablename__ = "vehicles"

        id: Mapped[uuid.UUID] = uuid_column()
        plate_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        normalized_plate: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
        color: Mapped[str | None] = mapped_column(String(30), nullable=True)
        make: Mapped[str | None] = mapped_column(String(50), nullable=True)
        model: Mapped[str | None] = mapped_column(String(50), nullable=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
        is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
        deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
        last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    class VehicleSighting(Base):
        __tablename__ = "vehicle_sightings"

        id: Mapped[uuid.UUID] = uuid_column()
        vehicle_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
        camera_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cameras.id"), index=True)
        plate_text: Mapped[str] = mapped_column(String(50), index=True)
        confidence: Mapped[float] = mapped_column(Float)
        crop_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
        metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
        normalized_plate: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
        is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
        deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

except ImportError:
    class Vehicle:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class VehicleSighting:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
