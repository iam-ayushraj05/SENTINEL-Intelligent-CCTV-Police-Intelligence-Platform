from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_recurring_alert_state"
down_revision = "0002_alert_recipients_deliveries"
branch_labels = None
depends_on = None


def upgrade():
    additions = [
        sa.Column("recipient_name", sa.String(200), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("status", sa.String(30), nullable=True, server_default="PENDING"),
        sa.Column("is_recurring", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column("recurrence_interval_seconds", sa.Integer(), nullable=True, server_default="300"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_message_id", sa.String(200), nullable=True),
        sa.Column("send_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
    ]
    for column in additions:
        op.add_column("alert_deliveries", column)

    op.execute(
        """
        UPDATE alert_deliveries
        SET recipient_name = COALESCE(
                (SELECT name FROM alert_recipients WHERE alert_recipients.id = alert_deliveries.recipient_id),
                'Unknown recipient'
            ),
            phone_number = COALESCE(
                (SELECT phone_number FROM phone_verifications pv JOIN alert_recipients ar ON ar.phone_verification_id = pv.id WHERE ar.id = alert_deliveries.recipient_id),
                ''
            ),
            status = CASE WHEN risk_level = 'HIGH' THEN 'ACTIVE' ELSE 'SENT' END,
            is_recurring = CASE WHEN risk_level = 'HIGH' THEN TRUE ELSE FALSE END,
            recurrence_interval_seconds = 300,
            started_at = created_at,
            send_count = 1
        """
    )

    op.create_index("ix_alert_deliveries_status", "alert_deliveries", ["status"])
    op.create_index("ix_alert_deliveries_next_send_at", "alert_deliveries", ["next_send_at"])

    op.create_table(
        "alert_send_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("alert_delivery_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("provider_message_id", sa.String(200), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["alert_delivery_id"], ["alert_deliveries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_id"], ["alert_recipients.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_alert_send_attempts_attempted_at", "alert_send_attempts", ["attempted_at"])


def downgrade():
    op.drop_index("ix_alert_send_attempts_attempted_at", table_name="alert_send_attempts")
    op.drop_table("alert_send_attempts")
    op.drop_index("ix_alert_deliveries_next_send_at", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_status", table_name="alert_deliveries")
    for column_name in [
        "last_error", "send_count", "provider_message_id", "stopped_at", "next_send_at",
        "last_sent_at", "started_at", "recurrence_interval_seconds", "is_recurring",
        "status", "phone_number", "recipient_name",
    ]:
        op.drop_column("alert_deliveries", column_name)
