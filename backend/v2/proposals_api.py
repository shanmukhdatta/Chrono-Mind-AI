"""Durable human approval and transactional schedule execution.

A model or background worker can request proposals but CANNOT call the approval
endpoint without a verified human user's Firebase session.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .calendar_api import conflict
from .db import get_or_create_user, get_session
from .models import FixedEvent, PlanProposal, Preference, ScheduleBlock, Task, User
from .planning_api import get_preview

router = APIRouter(prefix="/api/v2/plans", tags=["v2-approvals"])


class ProposalRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=14)


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


def present(plan: PlanProposal) -> dict:
    return {
        "id": plan.id,
        "status": plan.status,
        "created_at": plan.created_at.isoformat(),
        "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
        "blocks": plan.proposed_blocks,
        "unscheduled": plan.unscheduled,
        "committed_block_ids": plan.committed_block_ids,
    }


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

    pref = plan.preferences_snapshot
    zone = ZoneInfo(pref["timezone"])
    existing = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    busy = [(ensure_aware(block.starts_at), ensure_aware(block.ends_at), True) for block in existing]
    busy += [(ensure_aware(row.starts_at), ensure_aware(row.ends_at), False)
             for row in db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()]
    occupied_by_task = defaultdict(int)
    for block in existing:
        start = ensure_aware(block.starts_at)
        end = ensure_aware(block.ends_at)
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
    preview = get_preview(days=body.days, user=user, db=db)
    if not preview["blocks"]:
        raise HTTPException(409, "No unscheduled work fits this planning horizon")
    # Freeze the version of each affected task for approval-time conflict detection.
    ids = {row["task_id"] for row in preview["blocks"]}
    tasks = db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(ids))).all()
    versions = {task.id: task.version for task in tasks}
    plan = PlanProposal(
        owner_uid=uid, proposed_blocks=preview["blocks"],
        unscheduled=preview["unscheduled"],
        preferences_snapshot=current_prefs(db, uid),
        task_versions=versions,
        committed_block_ids=[],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return present(plan)


@router.get("")
def list_proposals(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    rows = db.scalars(select(PlanProposal).where(
        PlanProposal.owner_uid == user["uid"]
    ).order_by(PlanProposal.created_at.desc()).limit(30)).all()
    return [present(row) for row in rows]


@router.get("/{plan_id}")
def get_proposal(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    return present(read_proposal(db, user["uid"], plan_id))


@router.post("/{plan_id}/approve")
def approve_proposal(plan_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    plan = read_proposal(db, uid, plan_id, lock=True)
    if plan.status != "pending":
        raise HTTPException(409, "Only pending proposals can be approved")
    now = datetime.now(timezone.utc)
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
    db.commit()
    db.refresh(plan)
    return present(plan)
