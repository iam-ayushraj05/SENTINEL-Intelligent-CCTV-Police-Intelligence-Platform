from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_ai_pipeline_contract"
down_revision = "0003_recurring_alert_state"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("detections", sa.Column("frame_reference", sa.String(500), nullable=True))
    op.add_column("detections", sa.Column("metadata_json", sa.JSON(), nullable=True))
    op.create_table(
        "detection_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("track_code", sa.String(100), nullable=False, unique=True),
        sa.Column("object_class", sa.String(50), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_detection_tracks_track_code", "detection_tracks", ["track_code"])
    op.create_table(
        "detection_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["camera_id"], ["cameras.id"], ondelete="CASCADE"),
    )


def downgrade():
    op.drop_table("detection_events")
    op.drop_index("ix_detection_tracks_track_code", table_name="detection_tracks")
    op.drop_table("detection_tracks")
    op.drop_column("detections", "metadata_json")
    op.drop_column("detections", "frame_reference")
