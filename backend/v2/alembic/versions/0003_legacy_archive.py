"""Archive original V1 task data for migration audits.

Revision ID: 0003_legacy_archive
Revises: 0002_proposals
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_legacy_archive"
down_revision = "0002_proposals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_legacy_task_archive",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("legacy_id", sa.String(128), nullable=False),
        sa.Column("original_json", sa.Text(), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_uid", "legacy_id", name="uq_v2_legacy_archive_owner_id"))
    op.create_index("ix_v2_legacy_task_archive_owner_uid", "v2_legacy_task_archive", ["owner_uid"])


def downgrade():
    raise RuntimeError("Legacy migration audit data cannot be dropped automatically")
