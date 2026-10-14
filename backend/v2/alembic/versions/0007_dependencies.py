"""Task prerequisite graph.

Revision ID: 0007_dependencies
Revises: 0006_notifications
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_dependencies"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("v2_task_dependencies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("depends_on_id", sa.String(36), sa.ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("owner_uid", "task_id", "depends_on_id", name="uq_v2_task_dependency"),
        sa.CheckConstraint("task_id <> depends_on_id", name="task_no_self_dependency"))
    op.create_index("ix_v2_task_dependencies_owner_uid", "v2_task_dependencies", ["owner_uid"])
    op.create_index("ix_v2_dependency_owner_task", "v2_task_dependencies", ["owner_uid","task_id"])

def downgrade():
    raise RuntimeError("Task dependencies require backup and explicit migration review before removal")
