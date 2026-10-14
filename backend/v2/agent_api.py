"""Authenticated durable LangGraph planning runs backed by PostgreSQL checkpoints."""
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
from .models import PlanProposal, PlanningDecisionLog, Task, User
from .planning_api import get_preview
from .proposals_api import current_prefs

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/agent", tags=["v2-agent"])


class StartPlanningRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=14)


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
        proposal = PlanProposal(
            id=run_id, owner_uid=uid, proposed_blocks=preview["blocks"],
            unscheduled=preview["unscheduled"], task_versions=versions,
            preferences_snapshot=current_prefs(db, uid),
            planning_trace=preview.get("decision_trace", {}),
            committed_block_ids=[],
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


@router.post("/runs", status_code=201)
def begin_run(body: StartPlanningRequest, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    run_id = str(uuid4())
    config = thread_config(uid, run_id)
    try:
        with compiled_graph() as graph:
            result = graph.invoke({"owner_uid": uid, "run_id": run_id, "days": body.days}, config)
            config, snapshot = get_snapshot(graph, uid, run_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    # The proposal is already committed independently of the graph checkpoint.
    return {
        "run_id": run_id, "proposal_id": snapshot.values.get("proposal_id"),
        "status": "awaiting_review" if snapshot.next else snapshot.values.get("status"),
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
        if proposal.status not in ("approved", "rejected", "undone"):
            raise HTTPException(409, "Approve or reject the proposal before resuming")
        verdict = proposal.status
    with compiled_graph() as graph:
        config, snapshot = get_snapshot(graph, uid, run_id)
        if "await_human" not in snapshot.next:
            raise HTTPException(409, "Graph is not awaiting human review")
        result = graph.invoke(Command(resume=verdict), config)
        return {"run_id": run_id, "proposal_id": run_id, "status": result["status"]}
