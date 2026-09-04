import uuid
from datetime import datetime

try:
    from sqlalchemy import String, Boolean, DateTime, ForeignKey, Table, Column
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from app.models.base import Base, TimestampMixin, uuid_column

    user_roles = Table(
        "user_roles",
        Base.metadata,
        Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    role_permissions = Table(
        "role_permissions",
        Base.metadata,
        Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    class User(Base, TimestampMixin):
        __tablename__ = "users"

        id: Mapped[uuid.UUID] = uuid_column()
        username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
        email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
        full_name: Mapped[str] = mapped_column(String(200))
        hashed_password: Mapped[str] = mapped_column(String(300))
        badge_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
        department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
        role: Mapped[str] = mapped_column(String(50), default="OPERATOR")
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    class Role(Base):
        __tablename__ = "roles"

        id: Mapped[uuid.UUID] = uuid_column()
        name: Mapped[str] = mapped_column(String(50), unique=True)
        description: Mapped[str | None] = mapped_column(String(250), nullable=True)

    class Permission(Base):
        __tablename__ = "permissions"

        id: Mapped[uuid.UUID] = uuid_column()
        code: Mapped[str] = mapped_column(String(100), unique=True)
        description: Mapped[str | None] = mapped_column(String(250), nullable=True)

except ImportError:
    class User:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class Role:
        pass
    class Permission:
        pass
    user_roles = None
    role_permissions = None
