"""Add proposal revisions/digests, idempotent operation receipts, entity versions, and agent runs.

Revision ID: 0014_agentic_receipts_and_runs
Revises: 0013_focus_context
"""
from alembic import op
import sqlalchemy as sa

revision = "0014_agentic_receipts_and_runs"
down_revision = "0013_focus_context"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("v2_goals", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("v2_schedule_blocks", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("v2_fixed_events", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    op.add_column("v2_plan_proposals", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("v2_plan_proposals", sa.Column("proposal_digest", sa.String(64), nullable=True))
    op.add_column("v2_plan_proposals", sa.Column("operations", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("v2_plan_proposals", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_v2_proposal_owner_idem", "v2_plan_proposals", ["owner_uid", "idempotency_key"])
    op.drop_constraint("proposal_status", "v2_plan_proposals", type_="check")
    op.create_check_constraint(
        "proposal_status",
        "v2_plan_proposals",
        "status IN ('pending','approved','rejected','undone','cancelled','stale')",
    )

    op.create_table(
        "v2_operation_receipts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False, index=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("v2_plan_proposals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("expected_revision", sa.Integer(), nullable=True),
        sa.Column("proposal_digest", sa.String(64), nullable=True),
        sa.Column("operation_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("committed_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("verified_records", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("error_detail", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_uid", "idempotency_key", name="uq_v2_receipt_owner_idem"),
        sa.CheckConstraint(
            "status IN ('pending','committed_unverified','verified','verification_conflict','failed')",
            name="receipt_status",
        ),
    )
    op.create_index("ix_v2_receipt_owner_created", "v2_operation_receipts", ["owner_uid", "created_at"])

    op.create_table(
        "v2_agent_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_uid", sa.String(128), sa.ForeignKey("v2_users.uid"), nullable=False, index=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("proposal_id", sa.String(36), sa.ForeignKey("v2_plan_proposals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("receipt_id", sa.String(36), sa.ForeignKey("v2_operation_receipts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("step", sa.String(48), nullable=False, server_default="intake"),
        sa.Column("resolved_entities", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("clarification_state", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("source_revisions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("consent_epoch", sa.String(64), nullable=True),
        sa.Column("candidate_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("proposal_digest", sa.String(64), nullable=True),
        sa.Column("budgets", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_detail", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_uid", "request_id", name="uq_v2_agent_run_owner_req"),
        sa.CheckConstraint(
            "status IN ('pending','awaiting_clarification','awaiting_approval','rejected','cancelled',"
            "'stale','committed_unverified','verified','verification_conflict','no_feasible_plan','approved','undone')",
            name="agent_run_status",
        ),
    )
    op.create_index("ix_v2_agent_run_owner_created", "v2_agent_runs", ["owner_uid", "created_at"])


def downgrade():
    raise RuntimeError("Schema revisions cannot be automatically dropped in production")
