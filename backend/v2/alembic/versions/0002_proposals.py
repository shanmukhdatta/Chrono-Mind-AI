"""Durable approval proposals.

Revision ID: 0002_proposals
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_proposals"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_plan_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("proposed_blocks", sa.JSON(), nullable=False),
        sa.Column("unscheduled", sa.JSON(), nullable=False),
        sa.Column("task_versions", sa.JSON(), nullable=False),
        sa.Column("preferences_snapshot", sa.JSON(), nullable=False),
        sa.Column("committed_block_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending','approved','rejected','undone')", name="proposal_status"))
    op.create_index("ix_v2_plan_proposals_owner_uid", "v2_plan_proposals", ["owner_uid"])
    op.create_index("ix_v2_proposals_owner_created", "v2_plan_proposals", ["owner_uid", "created_at"])


def downgrade():
    raise RuntimeError("Downgrade disabled: proposal history must not be destroyed")
