"""Durable planning alternatives and human decision evidence.

Revision ID: 0010_planning_decisions
Revises: 0009_task_splitting
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_planning_decisions"
down_revision = "0009_task_splitting"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("v2_plan_proposals", sa.Column(
        "planning_trace", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
    ))
    op.alter_column("v2_plan_proposals", "planning_trace", server_default=None)
    op.create_table("v2_planning_decision_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("v2_plan_proposals.id"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("before_blocks", sa.JSON(), nullable=False),
        sa.Column("after_blocks", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_v2_planning_decision_logs_owner_uid", "v2_planning_decision_logs", ["owner_uid"])
    op.create_index("ix_v2_decision_owner_date", "v2_planning_decision_logs", ["owner_uid","recorded_at"])


def downgrade():
    raise RuntimeError("Planning decision evidence must not be destroyed automatically")
