import uuid

try:
    from sqlalchemy import String, Text
    from sqlalchemy.orm import Mapped, mapped_column
    from app.models.base import Base, TimestampMixin, uuid_column

    class SystemSetting(Base, TimestampMixin):
        __tablename__ = "system_settings"

        id: Mapped[uuid.UUID] = uuid_column()
        key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        value: Mapped[str] = mapped_column(Text)
        description: Mapped[str | None] = mapped_column(String(250), nullable=True)

except ImportError:
    class SystemSetting: pass
