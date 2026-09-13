"""Persist vehicle intelligence metadata and soft deletion."""

from alembic import op
import sqlalchemy as sa

revision = "0007_vehicle_intelligence"
down_revision = "0006_evidence_custody"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    vehicle_columns = {column["name"] for column in inspector.get_columns("vehicles")}
    sighting_columns = {column["name"] for column in inspector.get_columns("vehicle_sightings")}

    for name, column in {
        "metadata_json": sa.Column("metadata_json", sa.JSON(), nullable=True),
        "is_deleted": sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        "deleted_at": sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    }.items():
        if name not in vehicle_columns:
            op.add_column("vehicles", column)

    for name, column in {
        "normalized_plate": sa.Column("normalized_plate", sa.String(50), nullable=True),
        "metadata_json": sa.Column("metadata_json", sa.JSON(), nullable=True),
        "is_deleted": sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        "deleted_at": sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    }.items():
        if name not in sighting_columns:
            op.add_column("vehicle_sightings", column)

    op.create_index("ix_vehicle_sightings_normalized_plate", "vehicle_sightings", ["normalized_plate"], if_not_exists=True)
    op.create_index("ix_vehicles_is_deleted", "vehicles", ["is_deleted"], if_not_exists=True)


def downgrade():
    op.drop_index("ix_vehicles_is_deleted", table_name="vehicles")
    op.drop_index("ix_vehicle_sightings_normalized_plate", table_name="vehicle_sightings")
    for table, columns in {
        "vehicle_sightings": ["deleted_at", "is_deleted", "metadata_json", "normalized_plate"],
        "vehicles": ["deleted_at", "is_deleted", "metadata_json"],
    }.items():
        for column in columns:
            op.drop_column(table, column)
