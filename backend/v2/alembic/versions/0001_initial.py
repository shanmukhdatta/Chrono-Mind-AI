"""Initial isolated PostgreSQL V2 domain tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_users",
        sa.Column("uid", sa.String(128), primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("v2_goals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('active','paused','completed','archived')", name="goal_status"))
    op.create_index("ix_v2_goals_owner_uid", "v2_goals", ["owner_uid"])
    op.create_table("v2_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("goal_id", sa.String(36), sa.ForeignKey("v2_goals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("legacy_id", sa.String(128), nullable=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("importance", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recurrence_rule", sa.String(160), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_uid", "legacy_id", name="uq_v2_owner_legacy_task"),
        sa.CheckConstraint("duration_minutes > 0", name="task_positive_duration"),
        sa.CheckConstraint("status IN ('pending','completed','archived')", name="task_status"),
        sa.CheckConstraint("importance IN ('important','not_important')", name="task_importance"))
    op.create_index("ix_v2_tasks_owner_uid", "v2_tasks", ["owner_uid"])
    op.create_index("ix_v2_tasks_owner_status_deadline", "v2_tasks", ["owner_uid", "status", "deadline_at"])
    op.create_table("v2_schedule_blocks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="schedule_order"))
    op.create_index("ix_v2_schedule_blocks_owner_uid", "v2_schedule_blocks", ["owner_uid"])
    op.create_index("ix_v2_blocks_owner_start", "v2_schedule_blocks", ["owner_uid", "starts_at"])
    op.create_table("v2_fixed_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="fixed_event_order"))
    op.create_index("ix_v2_fixed_events_owner_uid", "v2_fixed_events", ["owner_uid"])
    op.create_index("ix_v2_events_owner_start", "v2_fixed_events", ["owner_uid", "starts_at"])
    op.create_table("v2_preferences",
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), primary_key=True),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("work_start", sa.Time(), nullable=False),
        sa.Column("work_end", sa.Time(), nullable=False),
        sa.Column("max_daily_minutes", sa.Integer(), nullable=False),
        sa.Column("min_break_minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint("work_end > work_start", name="preference_work_window"),
        sa.CheckConstraint("max_daily_minutes BETWEEN 60 AND 960", name="preference_daily_limit"))


def downgrade():
    raise RuntimeError("Downgrade disabled: restore a verified backup rather than dropping user data")
