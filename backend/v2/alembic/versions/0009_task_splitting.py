"""Explicit task splitting preference, defaulting to existing V2 behavior.

Revision ID: 0009_task_splitting
Revises: 0008_release_hardening
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_task_splitting"
down_revision = "0008_release_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("v2_tasks", sa.Column(
        "splittable", sa.Boolean(), nullable=False,
        server_default=sa.true()
    ))
    op.alter_column("v2_tasks", "splittable", server_default=None)


def downgrade():
    raise RuntimeError("Dropping task splitting preferences requires operator review")
