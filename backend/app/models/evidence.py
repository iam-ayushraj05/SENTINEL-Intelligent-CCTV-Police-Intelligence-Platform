import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, String, ForeignKey, Text
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

except ImportError:
    class Evidence: pass
