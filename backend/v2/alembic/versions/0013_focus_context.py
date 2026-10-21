"""Add task context_tags and preference focus_context for context-aware priority.

Revision ID: 0013_focus_context
Revises: 0012_subtasks_monthly
"""
from alembic import op
import sqlalchemy as sa

revision = "0013_focus_context"
down_revision = "0012_subtasks_monthly"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "v2_tasks",
        sa.Column("context_tags", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "v2_preferences",
        sa.Column("focus_context", sa.String(64), nullable=True),
    )


def downgrade():
    # Schema revisions cannot be automatically dropped in production.
    raise RuntimeError("Schema revisions cannot be automatically dropped in production")
