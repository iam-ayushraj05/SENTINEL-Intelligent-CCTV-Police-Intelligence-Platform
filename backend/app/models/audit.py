import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, String, Text
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, uuid_column

    class AuditLog(Base):
        __tablename__ = "audit_logs"

        id: Mapped[uuid.UUID] = uuid_column()
        username: Mapped[str] = mapped_column(String(100), index=True)
        action: Mapped[str] = mapped_column(String(150), index=True)
        resource: Mapped[str] = mapped_column(String(200))
        details: Mapped[str | None] = mapped_column(Text, nullable=True)
        ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
        result: Mapped[str] = mapped_column(String(30), default="SUCCESS")
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

except ImportError:
    class AuditLog:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
