"""Add parent_task_id to v2_tasks and expand recurrence frequency to support monthly.

Revision ID: 0012_subtasks_monthly
Revises: 0011_assistant_metrics
"""
from alembic import op
import sqlalchemy as sa

revision = "0012_subtasks_monthly"
down_revision = "0011_assistant_metrics"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("v2_tasks", sa.Column("parent_task_id", sa.String(36), sa.ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=True))
    op.create_index("ix_v2_tasks_owner_parent", "v2_tasks", ["owner_uid", "parent_task_id"])

    # Update check constraint on v2_recurrence_series if database supports dropping constraints
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("recurrence_frequency", "v2_recurrence_series", type_="check")
        op.create_check_constraint("recurrence_frequency", "v2_recurrence_series", "frequency IN ('daily', 'weekly', 'monthly')")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("recurrence_frequency", "v2_recurrence_series", type_="check")
        op.create_check_constraint("recurrence_frequency", "v2_recurrence_series", "frequency IN ('daily', 'weekly')")
    op.drop_index("ix_v2_tasks_owner_parent", table_name="v2_tasks")
    op.drop_column("v2_tasks", "parent_task_id")
