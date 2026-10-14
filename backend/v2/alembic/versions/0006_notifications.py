"""In-app notifications with owner-scoped idempotency.

Revision ID: 0006_notifications
Revises: 0005_focus
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_notifications"
down_revision = "0005_focus"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("v2_inapp_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("dedupe_key", sa.String(160), nullable=False),
        sa.Column("message", sa.String(300), nullable=False),
        sa.Column("source_task_id", sa.String(36), sa.ForeignKey("v2_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("owner_uid", "dedupe_key", name="uq_v2_notification_owner_key"))
    op.create_index("ix_v2_inapp_notifications_owner_uid", "v2_inapp_notifications", ["owner_uid"])
    op.create_index("ix_v2_notification_owner_created", "v2_inapp_notifications", ["owner_uid", "created_at"])

def downgrade():
    raise RuntimeError("Notification history cannot be dropped automatically")
