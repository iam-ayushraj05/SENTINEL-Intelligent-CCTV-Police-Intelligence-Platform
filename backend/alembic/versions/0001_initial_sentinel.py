from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_sentinel"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("camera_code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vms_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("protocol", sa.String(30), nullable=False, server_default="RTSP"),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("status", sa.String(30), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )
    op.create_index("ix_cameras_camera_code", "cameras", ["camera_code"])
    op.create_index("ix_cameras_status", "cameras", ["status"])

    op.create_table(
        "detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("object_type", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("track_id", sa.String(100)),
        sa.Column("bbox", sa.JSON()),
        sa.Column("metadata_json", sa.JSON()),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"]),
    )
    op.create_index("ix_detections_camera_timestamp", "detections", ["camera_id", "timestamp"])
    op.create_index("ix_detections_object_type", "detections", ["object_type"])

    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plate_number", sa.String(100)),
        sa.Column("plate_normalized", sa.String(100)),
        sa.Column("vehicle_type", sa.String(50)),
        sa.Column("color", sa.String(50)),
        sa.Column("make", sa.String(100)),
        sa.Column("model", sa.String(100)),
    )
    op.create_index("ix_vehicles_plate_normalized", "vehicles", ["plate_normalized"])

    op.create_table(
        "vehicle_sightings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plate_confidence", sa.Float()),
        sa.Column("vehicle_confidence", sa.Float()),
        sa.Column("frame_reference", sa.String(500)),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"]),
    )
    op.create_index("ix_vehicle_sightings_camera_timestamp", "vehicle_sightings", ["camera_id", "timestamp"])
    op.create_index("ix_vehicle_sightings_vehicle_timestamp", "vehicle_sightings", ["vehicle_id", "timestamp"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_code", sa.String(100), nullable=False, unique=True),
        sa.Column("alert_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("confidence", sa.Float()),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"]),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "watchlist_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_reference", sa.String(200), nullable=False),
        sa.Column("normalized_reference", sa.String(200), nullable=False),
        sa.Column("source_system", sa.String(100)),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"]),
    )
    op.create_index("ix_watchlist_entries_normalized_reference", "watchlist_entries", ["normalized_reference"])

    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_number", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("investigations")
    op.drop_index("ix_watchlist_entries_normalized_reference", table_name="watchlist_entries")
    op.drop_table("watchlist_entries")
    op.drop_table("watchlists")
    op.drop_index("ix_alerts_created_at", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_vehicle_sightings_vehicle_timestamp", table_name="vehicle_sightings")
    op.drop_index("ix_vehicle_sightings_camera_timestamp", table_name="vehicle_sightings")
    op.drop_table("vehicle_sightings")
    op.drop_index("ix_vehicles_plate_normalized", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_index("ix_detections_object_type", table_name="detections")
    op.drop_index("ix_detections_camera_timestamp", table_name="detections")
    op.drop_table("detections")
    op.drop_index("ix_cameras_status", table_name="cameras")
    op.drop_index("ix_cameras_camera_code", table_name="cameras")
    op.drop_table("cameras")
    op.drop_table("departments")
