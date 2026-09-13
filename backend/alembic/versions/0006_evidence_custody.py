from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_evidence_custody"
down_revision = "0005_notification_logs"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "evidences" not in inspector.get_table_names():
        op.create_table("evidences",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("file_name", sa.String(250), nullable=False),
            sa.Column("file_path", sa.String(500), nullable=False),
            sa.Column("mime_type", sa.String(100), nullable=False, server_default="application/octet-stream"),
            sa.Column("file_hash", sa.String(100)),
            sa.Column("investigation_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"]))
    op.add_column("evidences", sa.Column("evidence_code", sa.String(100), nullable=True))
    op.add_column("evidences", sa.Column("evidence_type", sa.String(50), nullable=False, server_default="DIGITAL"))
    op.add_column("evidences", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("evidences", sa.Column("status", sa.String(40), nullable=False, server_default="IN_CUSTODY"))
    op.add_column("evidences", sa.Column("current_location", sa.String(250), nullable=True))
    op.add_column("evidences", sa.Column("current_custodian", sa.String(150), nullable=True))
    op.add_column("evidences", sa.Column("metadata_json", sa.JSON(), nullable=True))
    op.execute(sa.text("UPDATE evidences SET evidence_code = 'EVD-LEGACY-' || id::text WHERE evidence_code IS NULL"))
    op.alter_column("evidences", "evidence_code", nullable=False)
    op.create_index("ix_evidences_evidence_code", "evidences", ["evidence_code"], unique=True)
    op.create_index("ix_evidences_status", "evidences", ["status"])
    op.create_table("evidence_custody_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_person", sa.String(150)), sa.Column("from_location", sa.String(250)),
        sa.Column("to_person", sa.String(150)), sa.Column("to_location", sa.String(250)),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("condition_before", sa.Text()),
        sa.Column("condition_after", sa.Text()), sa.Column("seal_condition", sa.String(150)),
        sa.Column("acknowledgement", sa.String(250)), sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidences.id"], ondelete="CASCADE"))
    op.create_index("ix_evidence_custody_events_evidence_id", "evidence_custody_events", ["evidence_id"])
    op.create_index("ix_evidence_custody_events_created_at", "evidence_custody_events", ["created_at"])


def downgrade():
    op.drop_table("evidence_custody_events")
    op.drop_index("ix_evidences_status", table_name="evidences")
    op.drop_index("ix_evidences_evidence_code", table_name="evidences")
    for column in ("metadata_json", "current_custodian", "current_location", "status", "description", "evidence_type", "evidence_code"):
        op.drop_column("evidences", column)