"""Opt-in behavior events and persistent focus sessions.

Revision ID: 0005_focus
Revises: 0004_recurrence
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_focus"
down_revision = "0004_recurrence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_behavior_consent",
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),primary_key=True),
        sa.Column("enabled",sa.Boolean(),nullable=False),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("v2_focus_sessions",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),nullable=False),
        sa.Column("task_id",sa.String(36),sa.ForeignKey("v2_tasks.id",ondelete="SET NULL"),nullable=True),
        sa.Column("status",sa.String(20),nullable=False),
        sa.Column("planned_seconds",sa.Integer(),nullable=False),
        sa.Column("actual_seconds",sa.Integer(),nullable=False),
        sa.Column("started_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("ended_at",sa.DateTime(timezone=True),nullable=True),
        sa.CheckConstraint("status IN ('active','completed','abandoned')",name="focus_status"),
        sa.CheckConstraint("planned_seconds BETWEEN 60 AND 14400",name="focus_planned_bounds"))
    op.create_index("ix_v2_focus_sessions_owner_uid","v2_focus_sessions",["owner_uid"])
    op.create_index("ix_v2_focus_owner_started","v2_focus_sessions",["owner_uid","started_at"])
    op.create_table("v2_behavior_events",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),nullable=False),
        sa.Column("kind",sa.String(40),nullable=False),
        sa.Column("hour_of_day",sa.Integer(),nullable=False),
        sa.Column("duration_seconds",sa.Integer(),nullable=False),
        sa.Column("happened_at",sa.DateTime(timezone=True),nullable=False),
        sa.CheckConstraint("hour_of_day BETWEEN 0 AND 23",name="behavior_valid_hour"),
        sa.CheckConstraint("duration_seconds >= 0",name="behavior_valid_duration"))
    op.create_index("ix_v2_behavior_events_owner_uid","v2_behavior_events",["owner_uid"])


def downgrade():
    raise RuntimeError("Behavior consent and focus history cannot be deleted automatically")
