"""Recurrence patterns, materialized tasks and skips.

Revision ID: 0004_recurrence
Revises: 0003_legacy_archive
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_recurrence"
down_revision = "0003_legacy_archive"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_recurrence_series",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),nullable=False),
        sa.Column("title",sa.String(160),nullable=False),
        sa.Column("duration_minutes",sa.Integer(),nullable=False),
        sa.Column("importance",sa.String(24),nullable=False),
        sa.Column("frequency",sa.String(12),nullable=False),
        sa.Column("weekdays",sa.String(20),nullable=False),
        sa.Column("timezone",sa.String(64),nullable=False),
        sa.Column("due_time",sa.Time(),nullable=True),
        sa.Column("start_date",sa.Date(),nullable=False),
        sa.Column("end_date",sa.Date(),nullable=True),
        sa.Column("active",sa.Boolean(),nullable=False),
        sa.Column("version",sa.Integer(),nullable=False),
        sa.CheckConstraint("frequency IN ('daily','weekly')",name="recurrence_frequency"),
        sa.CheckConstraint("duration_minutes BETWEEN 1 AND 1440",name="recurrence_duration"),
        sa.CheckConstraint("importance IN ('important','not_important')",name="recurrence_importance"))
    op.create_index("ix_v2_recurrence_series_owner_uid","v2_recurrence_series",["owner_uid"])
    op.create_table("v2_recurrence_occurrences",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),nullable=False),
        sa.Column("series_id",sa.String(36),sa.ForeignKey("v2_recurrence_series.id"),nullable=False),
        sa.Column("occurrence_date",sa.Date(),nullable=False),
        sa.Column("task_id",sa.String(36),sa.ForeignKey("v2_tasks.id"),nullable=False),
        sa.UniqueConstraint("series_id","occurrence_date",name="uq_v2_recurrence_occurrence"))
    op.create_index("ix_v2_recurrence_occurrences_owner_uid","v2_recurrence_occurrences",["owner_uid"])
    op.create_table("v2_recurrence_skips",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("owner_uid",sa.String(128),sa.ForeignKey("v2_users.uid"),nullable=False),
        sa.Column("series_id",sa.String(36),sa.ForeignKey("v2_recurrence_series.id"),nullable=False),
        sa.Column("occurrence_date",sa.Date(),nullable=False),
        sa.UniqueConstraint("series_id","occurrence_date",name="uq_v2_recurrence_skip"))
    op.create_index("ix_v2_recurrence_skips_owner_uid","v2_recurrence_skips",["owner_uid"])


def downgrade():
    raise RuntimeError("Recurrence lineage cannot be dropped automatically")
