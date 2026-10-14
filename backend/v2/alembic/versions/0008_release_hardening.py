"""Release hardening: schedule source stores full plan UUIDs.

Revision ID: 0008_release_hardening
Revises: 0007_dependencies
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_release_hardening"
down_revision = "0007_dependencies"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "v2_schedule_blocks", "source",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64), existing_nullable=False,
    )


def downgrade():
    raise RuntimeError("A downgrade could truncate persisted plan audit identifiers")
