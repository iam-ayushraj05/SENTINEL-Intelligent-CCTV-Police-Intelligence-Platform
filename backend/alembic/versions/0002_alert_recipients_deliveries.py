from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_alert_recipients_deliveries"
down_revision = "0001_initial_sentinel"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "phone_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=False, unique=True),
        sa.Column("otp", sa.String(6)),
        sa.Column("otp_expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_timestamp", sa.DateTime(timezone=True)),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("block_reason", sa.Text()),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_phone_verifications_phone_number", "phone_verifications", ["phone_number"])
    op.create_index("ix_phone_verifications_is_verified", "phone_verifications", ["is_verified"])

    op.create_table(
        "alert_recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone_verification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_type", sa.String(50), nullable=False, server_default="OPERATOR"),
        sa.Column("alert_preference", sa.String(50), nullable=False, server_default="ALL"),
        sa.Column("email", sa.String(200)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["phone_verification_id"], ["phone_verifications.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_recipients_is_active", "alert_recipients", ["is_active"])

    op.create_table(
        "emergency_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_code", sa.String(100), nullable=False, unique=True),
        sa.Column("incident_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("detection_source", sa.String(50), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True)),
        sa.Column("location_latitude", sa.Float()),
        sa.Column("location_longitude", sa.Float()),
        sa.Column("location_name", sa.String(300)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ai_confidence", sa.Float()),
        sa.Column("detected_objects", sa.JSON()),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("operator_comments", sa.Text()),
        sa.Column("evidence_urls", sa.JSON()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"]),
    )
    op.create_index("ix_emergency_incidents_incident_code", "emergency_incidents", ["incident_code"])
    op.create_index("ix_emergency_incidents_severity", "emergency_incidents", ["severity"])
    op.create_index("ix_emergency_incidents_status", "emergency_incidents", ["status"])

    op.create_table(
        "incident_timelines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_time", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.ForeignKeyConstraint(["incident_id"], ["emergency_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"]),
    )
    op.create_index("ix_incident_timelines_event_time", "incident_timelines", ["event_time"])

    op.create_table(
        "alert_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_level", sa.String(30), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("initial_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("follow_up_status", sa.String(30), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("follow_up_at", sa.DateTime(timezone=True)),
        sa.Column("feedback_message", sa.Text()),
        sa.Column("feedback_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["emergency_incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["alert_recipients.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_deliveries_follow_up_at", "alert_deliveries", ["follow_up_at"])


def downgrade():
    op.drop_index("ix_alert_deliveries_follow_up_at", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
    op.drop_index("ix_incident_timelines_event_time", table_name="incident_timelines")
    op.drop_table("incident_timelines")
    op.drop_index("ix_emergency_incidents_status", table_name="emergency_incidents")
    op.drop_index("ix_emergency_incidents_severity", table_name="emergency_incidents")
    op.drop_index("ix_emergency_incidents_incident_code", table_name="emergency_incidents")
    op.drop_table("emergency_incidents")
    op.drop_index("ix_alert_recipients_is_active", table_name="alert_recipients")
    op.drop_table("alert_recipients")
    op.drop_index("ix_phone_verifications_is_verified", table_name="phone_verifications")
    op.drop_index("ix_phone_verifications_phone_number", table_name="phone_verifications")
    op.drop_table("phone_verifications")
