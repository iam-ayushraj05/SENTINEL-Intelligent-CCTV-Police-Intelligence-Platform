import uuid
from datetime import datetime

try:
    from sqlalchemy import DateTime, String, JSON
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class GovernmentIntegrationRecord(Base, TimestampMixin):
        __tablename__ = "government_integration_records"

        id: Mapped[uuid.UUID] = uuid_column()
        external_system: Mapped[str] = mapped_column(String(100), index=True)
        query_reference: Mapped[str] = mapped_column(String(100), index=True)
        response_payload: Mapped[dict] = mapped_column(JSON)
        status: Mapped[str] = mapped_column(String(30), default="SUCCESS")

    class GovernmentSource(Base):
        __tablename__ = "government_sources"

        id: Mapped[uuid.UUID] = uuid_column()
        name: Mapped[str] = mapped_column(String(100))
        code: Mapped[str] = mapped_column(String(50), unique=True)
        status: Mapped[str] = mapped_column(String(30), default="CONNECTED")

    class ExternalRecord(Base):
        __tablename__ = "external_records"

        id: Mapped[uuid.UUID] = uuid_column()
        source_code: Mapped[str] = mapped_column(String(50))
        record_key: Mapped[str] = mapped_column(String(100))
        data_json: Mapped[dict] = mapped_column(JSON)

except ImportError:
    class GovernmentIntegrationRecord: pass
    class GovernmentSource: pass
    class ExternalRecord: pass
