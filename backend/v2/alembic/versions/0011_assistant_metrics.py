"""Per-user model routing, token usage, latency and optional configured cost.

Revision ID: 0011_assistant_metrics
Revises: 0010_planning_decisions
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_assistant_metrics"
down_revision = "0010_planning_decisions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("v2_assistant_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False),
        sa.Column("tier", sa.String(24), nullable=False),
        sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("model_id", sa.String(80), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_v2_assistant_metrics_owner_uid", "v2_assistant_metrics", ["owner_uid"])
    op.create_index("ix_v2_llm_metrics_owner_date", "v2_assistant_metrics", ["owner_uid", "recorded_at"])


def downgrade():
    raise RuntimeError("Usage audit records require an explicit retention/deletion plan")
