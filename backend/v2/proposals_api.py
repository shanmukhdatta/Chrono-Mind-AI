"""Durable human approval and transactional schedule execution.

A model or background worker can request proposals but CANNOT call the approval
endpoint without a verified human user's Firebase session.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .calendar_api import conflict
from .db import get_or_create_user, get_session
from .models import (
    FixedEvent,
    OperationReceipt,
    PlanProposal,
    PlanningDecisionLog,
    Preference,
    ScheduleBlock,
    Task,
    TaskDependency,
    User,
)
from .planning_api import get_preview

router = APIRouter(prefix="/api/v2/plans", tags=["v2-approvals"])


class ProposalRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=14)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class ApprovalRequest(BaseModel):
    expected_revision: int | None = Field(default=None, ge=1)
    proposal_digest: str | None = Field(default=None, min_length=8, max_length=64)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class MoveBlockRequest(BaseModel):
    block_index: int = Field(ge=0, le=499)
    starts_at: datetime


def compute_proposal_digest(
    proposed_blocks: list,
    operations: list,
    task_versions: dict,
    preferences_snapshot: dict,
    revision: int,
) -> str:
    payload = {
        "proposed_blocks": proposed_blocks,
        "operations": operations,
        "task_versions": task_versions,
        "preferences_snapshot": preferences_snapshot,
        "revision": revision,
    }
    raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def current_prefs(db: Session, uid: str) -> dict:
    pref = db.get(Preference, uid)
    if pref is None:
        return {
            "timezone": "Asia/Kolkata", "work_start": "08:00", "work_end": "22:00",
            "max_daily_minutes": 480, "min_break_minutes": 10,
        }
    return {
        "timezone": pref.timezone,
        "work_start": pref.work_start.strftime("%H:%M"),
        "work_end": pref.work_end.strftime("%H:%M"),
        "max_daily_minutes": pref.max_daily_minutes,
        "min_break_minutes": pref.min_break_minutes,
    }


def read_proposal(db: Session, uid: str, plan_id: str, lock: bool = False) -> PlanProposal:
    query = select(PlanProposal).where(PlanProposal.id == plan_id, PlanProposal.owner_uid == uid)
    if lock:
        query = query.with_for_update()
    item = db.scalar(query)
    if item is None:
        raise HTTPException(404, "Proposal not found")
    return item


def present(plan: PlanProposal, receipt: OperationReceipt | None = None) -> dict:
    digest = plan.proposal_digest or compute_proposal_digest(
        plan.proposed_blocks or [],
        plan.operations or [],
        plan.task_versions or {},
        plan.preferences_snapshot or {},
        plan.revision or 1,
    )
    out = {
        "id": plan.id,
        "status": plan.status,
        "revision": plan.revision or 1,
        "proposal_digest": digest,
        "created_at": plan.created_at.isoformat(),
        "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
        "blocks": plan.proposed_blocks,
        "operations": plan.operations or [],
        "unscheduled": plan.unscheduled,
        "decision_trace": plan.planning_trace,
        "committed_block_ids": plan.committed_block_ids,
    }
    if receipt is not None:
        out["receipt_id"] = receipt.id
        out["verification_status"] = receipt.status
        out["verified_records"] = receipt.verified_records
        if receipt.status == "verified":
            out["calendar_link"] = "/app/v2/calendar"
    return out


def ensure_aware(value: datetime | None):
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        return value.replace(tzinfo=timezone.utc)
    return value


def lock_owner(db: Session, uid: str) -> None:
    row = db.scalar(select(User).where(User.uid == uid).with_for_update())
    if row is None:
        raise HTTPException(409, "Account not provisioned")


def verify_candidate(db: Session, uid: str, plan: PlanProposal, now: datetime):
    """Validate every candidate again while holding PostgreSQL owner/task locks."""
    if current_prefs(db, uid) != plan.preferences_snapshot:
        raise HTTPException(409, "Planning preferences changed; generate a new proposal")
    if ensure_aware(plan.created_at) + timedelta(hours=1) < now:
        raise HTTPException(409, "Proposal expired; generate a new one")

    all_versions = plan.task_versions
    rows = db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(list(all_versions))).with_for_update()).all()
    tasks = {task.id: task for task in rows}
    if set(tasks) != set(all_versions):
        raise HTTPException(409, "The underlying tasks changed")
    for task_id, old_version in all_versions.items():
        if tasks[task_id].version != old_version or tasks[task_id].status != "pending":
            raise HTTPException(409, "A task changed; generate a new proposal")

    # Pending plans can outlive task hierarchy and prerequisite edits. Never
    # schedule a container or a newly blocked task just because its plan is old.
    container_ids = set(db.scalars(select(Task.parent_task_id).where(
        Task.owner_uid == uid, Task.parent_task_id.in_(list(tasks))
    )).all())
    if container_ids:
        raise HTTPException(409, "A planned task now has subtasks; generate a new proposal")
    prerequisites = db.scalars(select(TaskDependency).where(
        TaskDependency.owner_uid == uid, TaskDependency.task_id.in_(list(tasks))
    )).all()
    prerequisite_ids = {edge.depends_on_id for edge in prerequisites}
    states = dict(db.execute(select(Task.id, Task.status).where(
        Task.owner_uid == uid, Task.id.in_(prerequisite_ids)
    )).all()) if prerequisite_ids else {}
    if any(states.get(edge.depends_on_id) != "completed" for edge in prerequisites):
        raise HTTPException(409, "A planned task has an unfinished prerequisite")

    pref = plan.preferences_snapshot
    zone = ZoneInfo(pref["timezone"])
    existing = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    busy = [(ensure_aware(block.starts_at), ensure_aware(block.ends_at), True) for block in existing]
    busy += [(ensure_aware(row.starts_at), ensure_aware(row.ends_at), False)
             for row in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()]
    occupied_by_task = defaultdict(int)
    for block in existing:
        start, end = ensure_aware(block.starts_at), ensure_aware(block.ends_at)
        if end > now:
            occupied_by_task[block.task_id] += int((end - max(start, now)).total_seconds() // 60)

    staged = []
    occupied_per_day = defaultdict(int)
    for block in existing:
        start = ensure_aware(block.starts_at).astimezone(zone)
        end = ensure_aware(block.ends_at).astimezone(zone)
        if start.date() == end.date():
            occupied_per_day[start.date()] += int((end - start).total_seconds() // 60)

    for candidate in plan.proposed_blocks:
        task_id = candidate["task_id"]
        task = tasks.get(task_id)
        if task is None:
            raise HTTPException(409, "Proposal contains an unknown task")
        start = datetime.fromisoformat(candidate["starts_at"])
        end = datetime.fromisoformat(candidate["ends_at"])
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise HTTPException(409, "Invalid proposed time")
        minutes = int((end - start).total_seconds() // 60)
        if minutes <= 0 or minutes > 90 or int(candidate["duration_minutes"]) != minutes:
            raise HTTPException(409, "Invalid session duration")
        if start < now - timedelta(minutes=2):
            raise HTTPException(409, "Proposed session is now in the past; refresh the plan")
        deadline = ensure_aware(task.deadline_at)
        if deadline and end > deadline:
            raise HTTPException(409, "A session exceeds a task deadline")

        local_start, local_end = start.astimezone(zone), end.astimezone(zone)
        if (local_start.date() != local_end.date()
                or local_start.strftime("%H:%M") < pref["work_start"]
                or local_end.strftime("%H:%M") > pref["work_end"]):
            raise HTTPException(409, "Session is outside working hours")
        day = local_start.date()
        if occupied_per_day[day] + minutes > pref["max_daily_minutes"]:
            raise HTTPException(409, "Daily work limit exceeded")
        for before, after, is_task_work in busy:
            if start < after and end > before:
                raise HTTPException(409, "Calendar conflict; generate a new plan")
            if is_task_work:
                required = timedelta(minutes=pref["min_break_minutes"])
                if before >= end and before - end < required:
                    raise HTTPException(409, "Insufficient break before existing work")
                if start >= after and start - after < required:
                    raise HTTPException(409, "Insufficient break after existing work")
        occupied_by_task[task_id] += minutes
        if occupied_by_task[task_id] > task.duration_minutes:
            raise HTTPException(409, "More time was proposed than task duration")
        occupied_per_day[day] += minutes
        busy.append((start, end, True))
        staged.append((task_id, start, end))

    return staged


@router.post("", status_code=201)
def create_proposal(
    body: ProposalRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    get_or_create_user(db, uid)
    lock_owner(db, uid)
    if body.idempotency_key:
        existing = db.scalar(
            select(PlanProposal).where(
                PlanProposal.owner_uid == uid,
                PlanProposal.idempotency_key == body.idempotency_key,
            )
        )
        if existing is not None:
            return present(existing)
    preview = get_preview(days=body.days, user=user, db=db)
    if not preview["blocks"]:
        raise HTTPException(409, "No unscheduled work fits this planning horizon")
    # Freeze the version of each affected task for approval-time conflict detection.
    ids = {row["task_id"] for row in preview["blocks"]}
    tasks = db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(ids))).all()
    versions = {task.id: task.version for task in tasks}
    prefs_snap = current_prefs(db, uid)
    digest = compute_proposal_digest(preview["blocks"], [], versions, prefs_snap, 1)
    plan = PlanProposal(
        owner_uid=uid, proposed_blocks=preview["blocks"],
        unscheduled=preview["unscheduled"],
        preferences_snapshot=prefs_snap,
        task_versions=versions,
        planning_trace=preview.get("decision_trace", {}),
        committed_block_ids=[],
        revision=1,
        proposal_digest=digest,
        operations=[],
        idempotency_key=body.idempotency_key,
    )
    db.add(plan)
    db.flush()
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="proposed",
        reason_codes=["PRIORITY_SCORE", "CONSTRAINT_CHECKED", "USER_REVIEW_REQUIRED"],
        before_blocks=[], after_blocks=preview["blocks"],
    ))
    db.commit()
    db.refresh(plan)
    return present(plan)


@router.get("")
def list_proposals(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    rows = db.scalars(select(PlanProposal).where(
        PlanProposal.owner_uid == user["uid"]
    ).order_by(PlanProposal.created_at.desc()).limit(30)).all()
    return [present(row) for row in rows]


@router.get("/{plan_id}/history")
def proposal_history(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    read_proposal(db, uid, plan_id)
    records = db.scalars(select(PlanningDecisionLog).where(
        PlanningDecisionLog.owner_uid == uid, PlanningDecisionLog.proposal_id == plan_id
    ).order_by(PlanningDecisionLog.recorded_at, PlanningDecisionLog.id)).all()
    return [
        {
            "action": record.action, "reason_codes": record.reason_codes,
            "before_blocks": record.before_blocks, "after_blocks": record.after_blocks,
            "recorded_at": record.recorded_at,
        }
        for record in records
    ]


@router.get("/{plan_id}")
def get_proposal(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    return present(read_proposal(db, user["uid"], plan_id))


@router.put("/{plan_id}/blocks")
def move_proposed_block(
    plan_id: str, body: MoveBlockRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """A human may reposition one pending session; no calendar write occurs."""
    uid = user["uid"]
    lock_owner(db, uid)
    proposal = read_proposal(db, uid, plan_id, lock=True)
    if proposal.status != "pending":
        raise HTTPException(409, "Only pending proposals can be edited")
    original = list(proposal.proposed_blocks)
    if body.block_index >= len(original):
        raise HTTPException(404, "Proposed session not found")
    if body.starts_at.tzinfo is None or body.starts_at.utcoffset() is None:
        raise HTTPException(422, "Session start requires an explicit timezone offset")
    now = datetime.now(timezone.utc)
    begins = body.starts_at.astimezone(timezone.utc)
    if begins > ensure_aware(proposal.created_at) + timedelta(days=14):
        raise HTTPException(409, "Move is outside the 14-day horizon")
    edited = [dict(row) for row in original]
    row = edited[body.block_index]
    length = datetime.fromisoformat(row["ends_at"]) - datetime.fromisoformat(row["starts_at"])
    if length.total_seconds() <= 0:
        raise HTTPException(409, "Corrupted original proposal")
    row["starts_at"] = begins.isoformat()
    row["ends_at"] = (begins + length).isoformat()
    proposal.proposed_blocks = edited
    verify_candidate(db, uid, proposal, now)
    proposal.revision = (proposal.revision or 1) + 1
    proposal.proposal_digest = compute_proposal_digest(
        edited,
        proposal.operations or [],
        proposal.task_versions or {},
        proposal.preferences_snapshot or {},
        proposal.revision,
    )
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=proposal.id, action="edited",
        reason_codes=["USER_MOVED_SESSION", "CONSTRAINT_REVALIDATED"],
        before_blocks=original, after_blocks=edited,
    ))
    db.commit()
    db.refresh(proposal)
    return present(proposal)


def verify_committed_records(
    db: Session,
    uid: str,
    plan: PlanProposal,
    receipt: OperationReceipt,
) -> OperationReceipt:
    """Fresh domain read-back verifying committed IDs, owner, task, and intervals."""
    db.expire_all()
    ops = list(plan.operations or [])
    committed_ids = list(receipt.committed_ids or plan.committed_block_ids or [])
    if not committed_ids and not ops:
        receipt.status = "verified"
        receipt.verified_records = []
        receipt.updated_at = datetime.now(timezone.utc)
        db.commit()
        return receipt

    verified = []
    if ops:
        event_ids = [op["record_id"] for op in ops if op.get("entity_type") == "fixed_event" and op.get("record_id")]
        events_by_id = {
            e.id: e
            for e in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid, FixedEvent.id.in_(event_ids))).all()
        } if event_ids else {}
        blocks_by_id = {
            b.id: b
            for b in db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid, ScheduleBlock.id.in_(committed_ids))).all()
        } if committed_ids else {}

        for op in ops:
            if op["op_type"] == "move_fixed_event":
                ev = events_by_id.get(op["record_id"])
                if ev is None:
                    receipt.status = "verification_conflict"
                    receipt.error_detail = "Moved fixed event missing on read-back"
                    receipt.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    return receipt
                ev_s = ensure_aware(ev.starts_at).astimezone(timezone.utc).isoformat()
                ev_e = ensure_aware(ev.ends_at).astimezone(timezone.utc).isoformat()
                if ev_s != datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc).isoformat():
                    receipt.status = "verification_conflict"
                    receipt.error_detail = "Fixed event interval mismatch on read-back"
                    receipt.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    return receipt
                verified.append({"entity_type": "fixed_event", "id": ev.id, "owner_uid": ev.owner_uid, "starts_at": ev_s, "ends_at": ev_e})
            elif op["op_type"] == "move_schedule_block":
                blk = blocks_by_id.get(op["record_id"])
                if blk is None:
                    receipt.status = "verification_conflict"
                    receipt.error_detail = "Relocated block missing on read-back"
                    receipt.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    return receipt
                b_s = ensure_aware(blk.starts_at).astimezone(timezone.utc).isoformat()
                b_e = ensure_aware(blk.ends_at).astimezone(timezone.utc).isoformat()
                verified.append({"entity_type": "schedule_block", "id": blk.id, "owner_uid": blk.owner_uid, "task_id": blk.task_id, "starts_at": b_s, "ends_at": b_e, "source": blk.source})
            elif op["op_type"] == "add_schedule_block":
                matched = [b for b in blocks_by_id.values() if b.source == f"plan:{plan.id}" and b.task_id == op["task_id"] and ensure_aware(b.starts_at).astimezone(timezone.utc).isoformat() == datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc).isoformat()]
                if not matched:
                    receipt.status = "verification_conflict"
                    receipt.error_detail = "Added block missing on read-back"
                    receipt.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    return receipt
                b = matched[0]
                verified.append({"entity_type": "schedule_block", "id": b.id, "owner_uid": b.owner_uid, "task_id": b.task_id, "starts_at": ensure_aware(b.starts_at).astimezone(timezone.utc).isoformat(), "ends_at": ensure_aware(b.ends_at).astimezone(timezone.utc).isoformat(), "source": b.source})
        receipt.status = "verified"
        receipt.verified_records = verified
        receipt.error_detail = None
        receipt.updated_at = datetime.now(timezone.utc)
        db.commit()
        return receipt

    blocks = db.scalars(
        select(ScheduleBlock).where(
            ScheduleBlock.owner_uid == uid,
            ScheduleBlock.id.in_(committed_ids),
        )
    ).all() if committed_ids else []

    by_id = {b.id: b for b in blocks}
    if len(by_id) != len(committed_ids):
        receipt.status = "verification_conflict"
        receipt.error_detail = "Committed block count mismatch on fresh read-back"
        receipt.updated_at = datetime.now(timezone.utc)
        db.commit()
        return receipt

    for bid in committed_ids:
        b = by_id[bid]
        verified.append({
            "entity_type": "schedule_block",
            "id": b.id,
            "owner_uid": b.owner_uid,
            "task_id": b.task_id,
            "starts_at": ensure_aware(b.starts_at).astimezone(timezone.utc).isoformat(),
            "ends_at": ensure_aware(b.ends_at).astimezone(timezone.utc).isoformat(),
            "source": b.source,
        })
    receipt.status = "verified"
    receipt.verified_records = verified
    receipt.error_detail = None
    receipt.updated_at = datetime.now(timezone.utc)
    db.commit()
    return receipt


def _apply_operations_atomically(
    db: Session,
    uid: str,
    plan: PlanProposal,
    now: datetime,
) -> tuple[list[str], list[str]]:
    """Lock, version-check, final-state validate, and apply multi-record diff atomically."""
    if ensure_aware(plan.created_at) + timedelta(hours=1) < now:
        raise HTTPException(409, "Proposal expired; generate a new one")
    if current_prefs(db, uid) != plan.preferences_snapshot:
        raise HTTPException(409, "Planning preferences changed; generate a new proposal")

    ops = list(plan.operations or [])
    event_ids = {op["record_id"] for op in ops if op.get("entity_type") == "fixed_event" and op.get("record_id")}
    block_ids = {op["record_id"] for op in ops if op.get("entity_type") == "schedule_block" and op.get("record_id")}
    task_ids = set(plan.task_versions or {})

    events = {
        e.id: e
        for e in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid).with_for_update()).all()
    }
    blocks = {
        b.id: b
        for b in db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid).with_for_update()).all()
    }
    tasks = {
        t.id: t
        for t in db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(task_ids)).with_for_update()).all()
    } if task_ids else {}

    for tid, expected_v in (plan.task_versions or {}).items():
        if tid not in tasks or tasks[tid].version != expected_v or tasks[tid].status != "pending":
            raise HTTPException(409, "A task changed; generate a new proposal")

    # Version-check all referenced fixed events and schedule blocks
    for op in ops:
        if op["op_type"] == "move_fixed_event":
            ev = events.get(op["record_id"])
            if ev is None or ev.version != op["expected_version"]:
                raise HTTPException(409, "Target fixed event changed; generate a new proposal")
        elif op["op_type"] == "move_schedule_block":
            blk = blocks.get(op["record_id"])
            if blk is None or blk.version != op["expected_version"]:
                raise HTTPException(409, "A scheduled block changed; generate a new proposal")

    # Build simulated final calendar state
    final_events: dict[str, tuple[datetime, datetime]] = {
        eid: (ensure_aware(ev.starts_at).astimezone(timezone.utc), ensure_aware(ev.ends_at).astimezone(timezone.utc))
        for eid, ev in events.items()
    }
    final_blocks: list[tuple[str | None, str, datetime, datetime]] = [
        (bid, blk.task_id, ensure_aware(blk.starts_at).astimezone(timezone.utc), ensure_aware(blk.ends_at).astimezone(timezone.utc))
        for bid, blk in blocks.items()
        if bid not in block_ids
    ]

    for op in ops:
        if op["op_type"] == "move_fixed_event":
            ns = datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc)
            ne = datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc)
            if ns < now - timedelta(minutes=2) or ne <= ns:
                raise HTTPException(409, "Moved event time is invalid or in the past")
            final_events[op["record_id"]] = (ns, ne)
        elif op["op_type"] == "move_schedule_block":
            ns = datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc)
            ne = datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc)
            if ns < now - timedelta(minutes=2) or ne <= ns:
                raise HTTPException(409, "Moved block time is invalid or in the past")
            final_blocks.append((op["record_id"], op["task_id"], ns, ne))
        elif op["op_type"] == "add_schedule_block":
            ns = datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc)
            ne = datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc)
            if ns < now - timedelta(minutes=2) or ne <= ns:
                raise HTTPException(409, "Added block time is invalid or in the past")
            final_blocks.append((None, op["task_id"], ns, ne))

    # Final-state overlap validation across all fixed events and schedule blocks
    ev_list = sorted(final_events.items(), key=lambda x: x[1][0])
    for (_, (s1, e1)), (_, (s2, e2)) in zip(ev_list, ev_list[1:]):
        if s2 < e1:
            raise HTTPException(409, "Final calendar state has overlapping fixed commitments")

    blk_sorted = sorted(final_blocks, key=lambda x: x[2])
    for (_, _, s1, e1), (_, _, s2, e2) in zip(blk_sorted, blk_sorted[1:]):
        if s2 < e1:
            raise HTTPException(409, "Final calendar state has overlapping schedule blocks")

    for _, _, bs, be in blk_sorted:
        for _, (es, ee) in ev_list:
            if bs < ee and be > es:
                raise HTTPException(409, "Final calendar state has block conflicting with a fixed commitment")

    # Apply all mutations atomically in this transaction
    committed_block_ids: list[str] = []
    added_block_ids: list[str] = []
    for op in ops:
        if op["op_type"] == "move_fixed_event":
            ev = events[op["record_id"]]
            ev.starts_at = datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc)
            ev.ends_at = datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc)
            ev.version += 1
        elif op["op_type"] == "move_schedule_block":
            blk = blocks[op["record_id"]]
            blk.starts_at = datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc)
            blk.ends_at = datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc)
            blk.version += 1
            committed_block_ids.append(blk.id)
        elif op["op_type"] == "add_schedule_block":
            blk = ScheduleBlock(
                owner_uid=uid,
                task_id=op["task_id"],
                starts_at=datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc),
                ends_at=datetime.fromisoformat(op["after"]["ends_at"]).astimezone(timezone.utc),
                source="plan:" + plan.id,
            )
            db.add(blk)
            db.flush()
            committed_block_ids.append(blk.id)
            added_block_ids.append(blk.id)
    return committed_block_ids, added_block_ids


@router.post("/{plan_id}/approve")
def approve_proposal(
    plan_id: str,
    body: ApprovalRequest | None = Body(default=None),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    req = body or ApprovalRequest()
    lock_owner(db, uid)

    if req.idempotency_key:
        existing_receipt = db.scalar(
            select(OperationReceipt).where(
                OperationReceipt.owner_uid == uid,
                OperationReceipt.idempotency_key == req.idempotency_key,
            ).with_for_update()
        )
        if existing_receipt is not None:
            plan = read_proposal(db, uid, plan_id)
            if existing_receipt.status == "committed_unverified":
                try:
                    existing_receipt = verify_committed_records(db, uid, plan, existing_receipt)
                except Exception as exc:
                    existing_receipt.error_detail = f"Read-back verification pending: {type(exc).__name__}"
                    db.commit()
            return present(plan, existing_receipt)

    plan = read_proposal(db, uid, plan_id, lock=True)
    current_rev = plan.revision or 1
    current_digest = plan.proposal_digest or compute_proposal_digest(
        plan.proposed_blocks or [],
        plan.operations or [],
        plan.task_versions or {},
        plan.preferences_snapshot or {},
        current_rev,
    )
    if req.expected_revision is not None and req.expected_revision != current_rev:
        raise HTTPException(409, "Proposal revision is stale; review the latest draft")
    if req.proposal_digest is not None and req.proposal_digest != current_digest:
        raise HTTPException(409, "Proposal digest mismatch; review the latest draft")
    if plan.status != "pending":
        raise HTTPException(409, "Only pending proposals can be approved")

    now = datetime.now(timezone.utc)
    if plan.operations:
        ids, _ = _apply_operations_atomically(db, uid, plan, now)
    else:
        verified_blocks = verify_candidate(db, uid, plan, now)
        ids = []
        for task_id, start, end in verified_blocks:
            block = ScheduleBlock(owner_uid=uid, task_id=task_id, starts_at=start, ends_at=end, source="plan:" + plan.id)
            db.add(block)
            db.flush()
            ids.append(block.id)
    plan.committed_block_ids = ids
    plan.status = "approved"
    plan.approved_at = now
    plan.proposal_digest = current_digest

    idem_key = req.idempotency_key or f"approve:{plan.id}:rev:{current_rev}"
    receipt = OperationReceipt(
        owner_uid=uid,
        proposal_id=plan.id,
        idempotency_key=idem_key,
        expected_revision=current_rev,
        proposal_digest=current_digest,
        operation_type="approve_proposal",
        status="committed_unverified",
        committed_ids=ids,
        verified_records=[],
        created_at=now,
        updated_at=now,
    )
    db.add(receipt)
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="approved",
        reason_codes=["USER_APPROVED", "CONSTRAINT_REVALIDATED"],
        before_blocks=[], after_blocks=plan.proposed_blocks,
    ))
    db.commit()
    db.refresh(plan)
    db.refresh(receipt)

    try:
        receipt = verify_committed_records(db, uid, plan, receipt)
    except Exception as exc:
        receipt.error_detail = f"Read-back verification pending: {type(exc).__name__}"
        db.commit()
    return present(plan, receipt)


@router.post("/{plan_id}/verify")
def verify_proposal_receipt(
    plan_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Retry read-back verification only for an already committed proposal."""
    uid = user["uid"]
    plan = read_proposal(db, uid, plan_id)
    receipt = db.scalar(
        select(OperationReceipt)
        .where(OperationReceipt.owner_uid == uid, OperationReceipt.proposal_id == plan.id)
        .order_by(OperationReceipt.created_at.desc())
    )
    if receipt is None:
        raise HTTPException(404, "No operation receipt found for this proposal")
    if receipt.status == "verified":
        return present(plan, receipt)
    try:
        receipt = verify_committed_records(db, uid, plan, receipt)
    except Exception as exc:
        receipt.error_detail = f"Read-back verification pending: {type(exc).__name__}"
        db.commit()
    return present(plan, receipt)


@router.post("/{plan_id}/cancel")
def cancel_proposal(
    plan_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    lock_owner(db, uid)
    plan = read_proposal(db, uid, plan_id, lock=True)
    if plan.status != "pending":
        raise HTTPException(409, "Only pending proposals can be cancelled")
    plan.status = "cancelled"
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="cancelled",
        reason_codes=["USER_CANCELLED"],
        before_blocks=[], after_blocks=[],
    ))
    db.commit()
    db.refresh(plan)
    return present(plan)


@router.post("/{plan_id}/reject")
def reject_proposal(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    plan = read_proposal(db, uid, plan_id, lock=True)
    if plan.status != "pending":
        raise HTTPException(409, "Only pending proposals can be rejected")
    plan.status = "rejected"
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="rejected",
        reason_codes=["USER_REJECTED"],
        before_blocks=[], after_blocks=[],
    ))
    db.commit()
    db.refresh(plan)
    return present(plan)


@router.post("/{plan_id}/undo")
def undo_proposal(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    plan = read_proposal(db, uid, plan_id, lock=True)
    if plan.status != "approved":
        raise HTTPException(409, "Only approved plans can be undone")
    if plan.operations:
        ops = list(plan.operations)
        events = {
            e.id: e
            for e in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid).with_for_update()).all()
        }
        blocks = {
            b.id: b
            for b in db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid).with_for_update()).all()
        }
        # Guard: verify every modified/added record still matches post-commit state and version
        added_to_delete = []
        moved_block_ids = set()
        moved_event_ids = set()
        for op in ops:
            if op["op_type"] == "move_fixed_event":
                ev = events.get(op["record_id"])
                if ev is None or ev.version != op["expected_version"] + 1:
                    raise HTTPException(409, "Moved fixed event was modified; cannot undo automatically")
                if ensure_aware(ev.starts_at).astimezone(timezone.utc).isoformat() != datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc).isoformat():
                    raise HTTPException(409, "Moved fixed event position changed; cannot undo automatically")
                moved_event_ids.add(ev.id)
            elif op["op_type"] == "move_schedule_block":
                blk = blocks.get(op["record_id"])
                if blk is None or blk.version != op["expected_version"] + 1:
                    raise HTTPException(409, "Relocated block was modified; cannot undo automatically")
                if ensure_aware(blk.starts_at).astimezone(timezone.utc).isoformat() != datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc).isoformat():
                    raise HTTPException(409, "Relocated block position changed; cannot undo automatically")
                moved_block_ids.add(blk.id)
            elif op["op_type"] == "add_schedule_block":
                matched = [
                    b for b in blocks.values()
                    if b.source == f"plan:{plan.id}"
                    and b.task_id == op["task_id"]
                    and ensure_aware(b.starts_at).astimezone(timezone.utc).isoformat() == datetime.fromisoformat(op["after"]["starts_at"]).astimezone(timezone.utc).isoformat()
                ]
                if not matched:
                    raise HTTPException(409, "Added plan block was modified or deleted; cannot undo automatically")
                added_to_delete.append(matched[0])

        # Check restored positions don't conflict with any unrelated events/blocks added after commit
        restored_events = []
        for eid, ev in events.items():
            op = next((o for o in ops if o["op_type"] == "move_fixed_event" and o["record_id"] == eid), None)
            if op:
                restored_events.append((
                    datetime.fromisoformat(op["before"]["starts_at"]).astimezone(timezone.utc),
                    datetime.fromisoformat(op["before"]["ends_at"]).astimezone(timezone.utc),
                ))
            else:
                restored_events.append((ensure_aware(ev.starts_at).astimezone(timezone.utc), ensure_aware(ev.ends_at).astimezone(timezone.utc)))

        delete_ids = {b.id for b in added_to_delete}
        restored_blocks = []
        for bid, blk in blocks.items():
            if bid in delete_ids:
                continue
            op = next((o for o in ops if o["op_type"] == "move_schedule_block" and o["record_id"] == bid), None)
            if op:
                restored_blocks.append((
                    datetime.fromisoformat(op["before"]["starts_at"]).astimezone(timezone.utc),
                    datetime.fromisoformat(op["before"]["ends_at"]).astimezone(timezone.utc),
                ))
            else:
                restored_blocks.append((ensure_aware(blk.starts_at).astimezone(timezone.utc), ensure_aware(blk.ends_at).astimezone(timezone.utc)))

        for bs, be in restored_blocks:
            for es, ee in restored_events:
                if bs < ee and be > es:
                    raise HTTPException(409, "Old position now conflicts with another commitment; cannot undo")

        # Apply guarded inverse updates
        for blk in added_to_delete:
            db.delete(blk)
        for op in ops:
            if op["op_type"] == "move_fixed_event":
                ev = events[op["record_id"]]
                ev.starts_at = datetime.fromisoformat(op["before"]["starts_at"]).astimezone(timezone.utc)
                ev.ends_at = datetime.fromisoformat(op["before"]["ends_at"]).astimezone(timezone.utc)
                ev.version += 1
            elif op["op_type"] == "move_schedule_block":
                blk = blocks[op["record_id"]]
                blk.starts_at = datetime.fromisoformat(op["before"]["starts_at"]).astimezone(timezone.utc)
                blk.ends_at = datetime.fromisoformat(op["before"]["ends_at"]).astimezone(timezone.utc)
                blk.version += 1

        plan.status = "undone"
        db.add(PlanningDecisionLog(
            owner_uid=uid, proposal_id=plan.id, action="undone",
            reason_codes=["USER_REQUESTED_UNDO", "GUARDED_INVERSE_RESTORED"],
            before_blocks=plan.proposed_blocks, after_blocks=[],
        ))
        db.commit()
        db.refresh(plan)
        return present(plan)

    original = {(row["task_id"], row["starts_at"], row["ends_at"]) for row in plan.proposed_blocks}
    blocks = db.scalars(select(ScheduleBlock).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.id.in_(plan.committed_block_ids)
    ).with_for_update()).all()
    if len(blocks) != len(plan.committed_block_ids):
        raise HTTPException(409, "Scheduled blocks have changed; manual recovery required")
    for block in blocks:
        record = (block.task_id, ensure_aware(block.starts_at).astimezone(timezone.utc).isoformat(),
                  ensure_aware(block.ends_at).astimezone(timezone.utc).isoformat())
        if block.source != "plan:" + plan.id or record not in original:
            raise HTTPException(409, "Plan blocks were modified; cannot undo automatically")
        db.delete(block)
    plan.status = "undone"
    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="undone",
        reason_codes=["USER_REQUESTED_UNDO", "ORIGINAL_BLOCKS_INTACT"],
        before_blocks=plan.proposed_blocks, after_blocks=[],
    ))
    db.commit()
    db.refresh(plan)
    return present(plan)
