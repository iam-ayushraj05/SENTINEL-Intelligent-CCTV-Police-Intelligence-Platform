import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, func
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class TimestampMixin:
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def uuid_column():
        return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

except ImportError:
    class Base:
        metadata = type("Metadata", (), {"create_all": lambda *args, **kwargs: None})()

    class TimestampMixin:
        created_at = None
        updated_at = None

    def uuid_column():
        return None

    def mapped_column(*args, **kwargs):
        return None

    Mapped = type("Mapped", (), {})
