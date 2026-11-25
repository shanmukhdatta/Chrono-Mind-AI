"""Authenticated durable LangGraph planning runs backed by PostgreSQL checkpoints."""
from datetime import datetime, timezone
import logging
import os
from contextlib import contextmanager
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .agent_graph import build_planner_graph
from .db import engine, get_or_create_user
from .models import AgentRun, OperationReceipt, PlanProposal, PlanningDecisionLog, Task, User
from .planning_api import get_preview
from .proposals_api import compute_proposal_digest, current_prefs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/agent", tags=["v2-agent"])


class StartPlanningRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=14)
    request_id: str | None = Field(default=None, min_length=1, max_length=128)


def checkpoint_uri():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise HTTPException(503, "V2 PostgreSQL database is not configured")
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url[len("postgresql+psycopg://"):]
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def load_preview(uid: str, days: int) -> dict:
    with Session(engine()) as db:
        return get_preview(days=days, user={"uid": uid}, db=db)


def persist_proposal(uid: str, run_id: str, preview: dict) -> str:
    """Idempotent graph node: a crash/replay cannot duplicate an approval proposal."""
    with Session(engine()) as db:
        get_or_create_user(db, uid)
        db.scalar(select(User).where(User.uid == uid).with_for_update())
        old = db.get(PlanProposal, run_id)
        if old is not None:
            if old.owner_uid != uid:
                raise HTTPException(403, "Proposal belongs to another account")
            return old.id
        affected = {row["task_id"] for row in preview["blocks"]}
        rows = db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(affected))).all()
        versions = {task.id: task.version for task in rows}
        if set(versions) != affected:
            raise HTTPException(409, "Tasks changed while the proposal was prepared")
        prefs_snap = current_prefs(db, uid)
        digest = compute_proposal_digest(preview["blocks"], [], versions, prefs_snap, 1)
        proposal = PlanProposal(
            id=run_id, owner_uid=uid, proposed_blocks=preview["blocks"],
            unscheduled=preview["unscheduled"], task_versions=versions,
            preferences_snapshot=prefs_snap,
            planning_trace=preview.get("decision_trace", {}),
            committed_block_ids=[],
            revision=1,
            proposal_digest=digest,
            operations=[],
        )
        db.add(proposal)
        db.flush()
        db.add(PlanningDecisionLog(
            owner_uid=uid, proposal_id=run_id, action="proposed",
            reason_codes=["AGENT_GENERATED", "VALIDATED", "HUMAN_REVIEW_REQUIRED"],
            before_blocks=[], after_blocks=preview["blocks"],
        ))
        db.commit()
        return run_id


@contextmanager
def compiled_graph():
    uri = checkpoint_uri()
    # Setup is an explicit operator action; never mutate checkpointer tables here.
    with PostgresSaver.from_conn_string(uri) as checkpointer:
        yield build_planner_graph(load_preview, persist_proposal, checkpointer)


def thread_config(uid: str, run_id: str):
    return {"configurable": {"thread_id": uid + ":" + run_id}}


def get_snapshot(graph, uid: str, run_id: str):
    config = thread_config(uid, run_id)
    snapshot = graph.get_state(config)
    if not snapshot.values or snapshot.values.get("owner_uid") != uid:
        raise HTTPException(404, "Agent run not found")
    return config, snapshot


def _sync_agent_run(
    uid: str,
    run_id: str,
    snapshot_values: dict,
    *,
    is_awaiting: bool,
    request_id: str | None = None,
):
    """Persist or update the owner-scoped AgentRun metadata record."""
    now = datetime.now(timezone.utc)
    with Session(engine()) as db:
        get_or_create_user(db, uid)
        run = db.get(AgentRun, run_id)
        proposal_id = snapshot_values.get("proposal_id")
        proposal = db.get(PlanProposal, proposal_id) if proposal_id else None
        receipt = db.scalar(
            select(OperationReceipt)
            .where(OperationReceipt.owner_uid == uid, OperationReceipt.proposal_id == proposal_id)
            .order_by(OperationReceipt.created_at.desc())
        ) if proposal_id else None

        if is_awaiting:
            run_status = "awaiting_approval"
        else:
            raw_status = snapshot_values.get("status") or "pending"
            run_status = "awaiting_approval" if raw_status == "awaiting_review" else raw_status
        if receipt is not None and receipt.status in ("committed_unverified", "verified", "verification_conflict"):
            run_status = receipt.status

        if run is None:
            run = AgentRun(
                id=run_id,
                owner_uid=uid,
                request_id=request_id,
                proposal_id=proposal_id,
                receipt_id=receipt.id if receipt else None,
                status=run_status,
                step=snapshot_values.get("step", "store"),
                resolved_entities=snapshot_values.get("resolved_entities", {}),
                clarification_state=snapshot_values.get("clarification_state", {}),
                source_revisions=proposal.task_versions if proposal else {},
                consent_epoch=snapshot_values.get("consent_epoch"),
                candidate_ids=snapshot_values.get("candidate_ids", []),
                proposal_digest=proposal.proposal_digest if proposal else None,
                budgets=snapshot_values.get("budgets", {"max_attempts": 3}),
                error_detail=snapshot_values.get("validation_error") or None,
                created_at=now,
                updated_at=now,
            )
            db.add(run)
        else:
            run.proposal_id = proposal_id or run.proposal_id
            run.receipt_id = receipt.id if receipt else run.receipt_id
            run.status = run_status
            run.step = snapshot_values.get("step", run.step)
            run.proposal_digest = proposal.proposal_digest if proposal else run.proposal_digest
            run.updated_at = now
        db.commit()


@router.get("/runs")
def list_runs(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    with Session(engine()) as db:
        rows = db.scalars(
            select(AgentRun)
            .where(AgentRun.owner_uid == uid)
            .order_by(AgentRun.created_at.desc())
            .limit(30)
        ).all()
        return [
            {
                "run_id": r.id,
                "request_id": r.request_id,
                "proposal_id": r.proposal_id,
                "receipt_id": r.receipt_id,
                "status": r.status,
                "step": r.step,
                "proposal_digest": r.proposal_digest,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in rows
        ]


@router.post("/runs", status_code=201)
def begin_run(body: StartPlanningRequest, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    if body.request_id:
        with Session(engine()) as db:
            existing = db.scalar(
                select(AgentRun).where(AgentRun.owner_uid == uid, AgentRun.request_id == body.request_id)
            )
            if existing is not None:
                return {
                    "run_id": existing.id,
                    "proposal_id": existing.proposal_id,
                    "status": "awaiting_review" if existing.status == "awaiting_approval" else existing.status,
                    "run_status": existing.status,
                    "requires_human_approval": existing.status == "awaiting_approval",
                    "proposal_digest": existing.proposal_digest,
                    "reason": existing.error_detail,
                }
    run_id = str(uuid4())
    config = thread_config(uid, run_id)
    try:
        with compiled_graph() as graph:
            result = graph.invoke(
                {"owner_uid": uid, "run_id": run_id, "request_id": body.request_id or run_id, "days": body.days},
                config,
            )
            config, snapshot = get_snapshot(graph, uid, run_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    _sync_agent_run(uid, run_id, snapshot.values, is_awaiting=bool(snapshot.next), request_id=body.request_id)
    # The proposal is already committed independently of the graph checkpoint.
    return {
        "run_id": run_id, "proposal_id": snapshot.values.get("proposal_id"),
        "status": "awaiting_review" if snapshot.next else snapshot.values.get("status"),
        "run_status": "awaiting_approval" if snapshot.next else snapshot.values.get("status"),
        "requires_human_approval": bool(snapshot.next),
        "reason": snapshot.values.get("validation_error") or None,
    }


@router.get("/runs/{run_id}")
def read_run(run_id: str, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    with compiled_graph() as graph:
        _, snapshot = get_snapshot(graph, uid, run_id)
        return {
            "run_id": run_id, "proposal_id": snapshot.values.get("proposal_id"),
            "status": "awaiting_review" if snapshot.next else snapshot.values.get("status"),
            "next_nodes": list(snapshot.next),
        }


@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str, user: dict = Depends(get_current_user)):
    """Cancel an unapproved run before commit; prevents any subsequent write."""
    uid = user["uid"]
    with Session(engine()) as db:
        proposal = db.scalar(
            select(PlanProposal).where(PlanProposal.id == run_id, PlanProposal.owner_uid == uid).with_for_update()
        )
        if proposal is not None:
            if proposal.status != "pending":
                raise HTTPException(409, f"Cannot cancel proposal in status '{proposal.status}'")
            proposal.status = "cancelled"
            db.add(PlanningDecisionLog(
                owner_uid=uid, proposal_id=proposal.id, action="cancelled",
                reason_codes=["USER_CANCELLED_RUN"], before_blocks=[], after_blocks=[],
            ))
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.owner_uid == uid).with_for_update())
        if run is not None:
            if run.status in ("committed_unverified", "verified", "approved"):
                raise HTTPException(409, "Cannot cancel an already committed run")
            run.status = "cancelled"
            run.updated_at = datetime.now(timezone.utc)
        db.commit()
    try:
        with compiled_graph() as graph:
            config, snapshot = get_snapshot(graph, uid, run_id)
            if "await_human" in snapshot.next:
                graph.invoke(Command(resume="cancelled"), config)
    except HTTPException:
        pass
    return {"run_id": run_id, "proposal_id": run_id, "status": "cancelled"}


@router.post("/runs/{run_id}/resume")
def resume_run(run_id: str, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    # The caller cannot provide a verdict. Read it from the user-owned approval record.
    with Session(engine()) as db:
        proposal = db.scalar(select(PlanProposal).where(
            PlanProposal.id == run_id, PlanProposal.owner_uid == uid
        ))
        if proposal is None:
            raise HTTPException(404, "Agent proposal not found")
        if proposal.status not in ("approved", "rejected", "undone", "cancelled", "stale"):
            raise HTTPException(409, "Approve or reject the proposal before resuming")
        verdict = proposal.status
        receipt = db.scalar(
            select(OperationReceipt)
            .where(OperationReceipt.owner_uid == uid, OperationReceipt.proposal_id == proposal.id)
            .order_by(OperationReceipt.created_at.desc())
        )
        reconciled_status = receipt.status if receipt and receipt.status in ("committed_unverified", "verified", "verification_conflict") else verdict
    with compiled_graph() as graph:
        config, snapshot = get_snapshot(graph, uid, run_id)
        if "await_human" not in snapshot.next:
            raise HTTPException(409, "Graph is not awaiting human review")
        result = graph.invoke(Command(resume=verdict), config)
        _sync_agent_run(uid, run_id, {**result, "status": reconciled_status}, is_awaiting=False)
        return {"run_id": run_id, "proposal_id": run_id, "status": result["status"], "receipt_status": reconciled_status}
