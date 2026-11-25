"""Read-only planning preview backed by PostgreSQL. Does not commit calendar changes."""
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import (
    BehaviorConsent, BehaviorEvent, FixedEvent, Goal, InAppNotification,
    PlanProposal, PlanningDecisionLog, Preference, RecurrenceOccurrence, RecurrenceSeries,
    ScheduleBlock, Task, TaskDependency, User
)
from .priority import context_matches, score_task
from .personalization import preferred_work_hour
from .planner import BusyInterval, PlanningPreferences, PlanningTask
from .replanning import choose_schedule

router = APIRouter(prefix="/api/v2/planning", tags=["v2-planning"])


def _aware(instant: datetime | None) -> datetime | None:
    if instant is not None and (instant.tzinfo is None or instant.utcoffset() is None):
        # SQLite test adapters lose tzinfo; production PostgreSQL TIMESTAMPTZ is aware.
        return instant.replace(tzinfo=timezone.utc)
    return instant


@router.get("/preview")
def get_preview(
    days: int = Query(7, ge=1, le=14),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    consent = db.get(BehaviorConsent, uid)
    preferred = None
    if consent is not None and consent.enabled:
        signals = db.scalars(select(BehaviorEvent).where(
            BehaviorEvent.owner_uid == uid, BehaviorEvent.kind == "focus_completed"
        ).order_by(BehaviorEvent.happened_at.desc()).limit(90)).all()
        preferred = preferred_work_hour(
            [(event.hour_of_day, event.duration_seconds) for event in signals]
        )
    pref = db.get(Preference, uid)
    if pref is None:
        # Read-only preview never provisions a database user or changes preferences.
        opts = PlanningPreferences("Asia/Kolkata", time(8), time(22), 480, 10, preferred)
    else:
        opts = PlanningPreferences(
            pref.timezone, pref.work_start, pref.work_end,
            pref.max_daily_minutes, pref.min_break_minutes, preferred
        )

    rows = db.scalars(select(Task).where(Task.owner_uid == uid, Task.status == "pending")).all()
    # A decomposed parent is a container, not additional work to allocate.
    # Children carry its effort; otherwise the planner would double-book it.
    container_ids = set(db.scalars(select(Task.parent_task_id).where(
        Task.owner_uid == uid, Task.parent_task_id.is_not(None)
    )).all())
    rows = [task for task in rows if task.id not in container_ids]
    blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    events = db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()

    dependencies = db.scalars(select(TaskDependency).where(TaskDependency.owner_uid == uid)).all()
    prerequisite_ids = {item.depends_on_id for item in dependencies}
    known = {
        task.id: task.status for task in db.scalars(select(Task).where(
            Task.owner_uid == uid, Task.id.in_(prerequisite_ids)
        )).all()
    } if prerequisite_ids else {}
    blockers = defaultdict(list)
    for dependency in dependencies:
        if known.get(dependency.depends_on_id) != "completed":
            blockers[dependency.task_id].append(dependency.depends_on_id)
    # Preserve parent prerequisite constraints after decomposition:
    # if a parent task is blocked by an unfinished prerequisite, its subtasks are also blocked.
    for row in rows:
        if row.parent_task_id and blockers.get(row.parent_task_id):
            for prereq_id in blockers[row.parent_task_id]:
                if prereq_id not in blockers[row.id]:
                    blockers[row.id].append(prereq_id)

    # Carry recurrence occurrence dates into earliest-start constraints so future occurrences never start early.
    occ_rows = db.scalars(select(RecurrenceOccurrence).where(
        RecurrenceOccurrence.owner_uid == uid
    )).all()
    series_tz_map = {
        s.id: s.timezone for s in db.scalars(select(RecurrenceSeries).where(
            RecurrenceSeries.owner_uid == uid
        )).all()
    }
    earliest_by_task: dict[str, datetime] = {}
    for occ in occ_rows:
        tz = ZoneInfo(series_tz_map.get(occ.series_id, opts.timezone))
        earliest_by_task[occ.task_id] = datetime.combine(occ.occurrence_date, time(0, 0), tz).astimezone(timezone.utc)

    generated = datetime.now(timezone.utc)
    scheduled = defaultdict(int)
    postponed = defaultdict(int)
    occupied = []
    for block in blocks:
        start = _aware(block.starts_at)
        end = _aware(block.ends_at)
        # Missed sessions are not completed work; allow new proposals for unfinished tasks.
        if end > generated:
            scheduled[block.task_id] += int((end - max(start, generated)).total_seconds() // 60)
        else:
            # A past session for still-pending work is one recorded postponement.
            postponed[block.task_id] += 1
        occupied.append(BusyInterval(start, end, counts_as_work=True))
    for event in events:
        occupied.append(BusyInterval(_aware(event.starts_at), _aware(event.ends_at)))

    active_goal_ids = set(db.scalars(select(Goal.id).where(
        Goal.owner_uid == uid, Goal.status == "active"
    )).all())
    dependent_counts = defaultdict(int)
    for dep in dependencies:
        dependent_counts[dep.depends_on_id] += 1

    tasks = [
        PlanningTask(
            row.id, row.title, max(0, row.duration_minutes - scheduled[row.id]),
            row.importance, _aware(row.deadline_at),
            ("Prerequisite tasks are not yet completed: " + ", ".join(sorted(blockers[row.id])))
            if blockers[row.id] else None,
            score_task(
                row.importance, _aware(row.deadline_at),
                row.goal_id in active_goal_ids, generated,
                postponements=postponed[row.id],
                dependent_count=dependent_counts[row.id],
                is_blocked=bool(blockers[row.id]),
                duration_minutes=row.duration_minutes,
                context_match=context_matches(pref.focus_context if pref else None, row.context_tags),
                splittable=row.splittable,
            ).score,
            row.splittable,
            earliest_by_task.get(row.id),
        )
        for row in rows
    ]
    suggestion, decision_trace = choose_schedule(tasks, occupied, opts, generated, days)
    return {
        "generated_at": generated.isoformat(),
        "timezone": opts.timezone,
        "changes_committed": False,
        "decision_trace": decision_trace,
        "personalization": {
            "applied": preferred is not None,
            "preferred_hour": preferred,
            "method": "opt-in focus-hour heuristic" if preferred is not None else "off or insufficient samples",
        },
        "blocks": [
            {
                "task_id": block.task_id,
                "title": block.title,
                "starts_at": block.starts_at.astimezone(timezone.utc).isoformat(),
                "ends_at": block.ends_at.astimezone(timezone.utc).isoformat(),
                "duration_minutes": block.duration_minutes,
            }
            for block in suggestion.blocks
        ],
        "unscheduled": [
            {
                "task_id": task.task_id,
                "title": task.title,
                "remaining_minutes": task.remaining_minutes,
                "reason": task.reason,
            }
            for task in suggestion.unscheduled
        ],
    }


class TargetedPreviewRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=36)
    requested_minutes: int | None = Field(default=None, ge=1, le=90)
    window_start: datetime | None = None
    window_end: datetime | None = None
    exact_minutes: bool = False


def get_targeted_preview(
    db: Session,
    uid: str,
    task_id: str,
    *,
    requested_minutes: int | None = None,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    exact_minutes: bool = False,
    now_utc: datetime | None = None,
) -> dict:
    """Preview scheduling for one specific existing task within an optional date window."""
    generated = _aware(now_utc) or datetime.now(timezone.utc)
    task = db.scalar(select(Task).where(Task.owner_uid == uid, Task.id == task_id))
    if task is None:
        raise HTTPException(404, "Target task not found")
    if task.status != "pending":
        raise HTTPException(409, f"Task '{task.title}' is {task.status}, not pending")

    has_children = db.scalar(
        select(Task.id).where(Task.owner_uid == uid, Task.parent_task_id == task_id).limit(1)
    )
    if has_children is not None:
        return {
            "generated_at": generated.isoformat(),
            "timezone": _user_timezone_or_default(db, uid),
            "changes_committed": False,
            "target_task_id": task_id,
            "blocks": [],
            "unscheduled": [{
                "task_id": task_id,
                "title": task.title,
                "remaining_minutes": task.duration_minutes,
                "reason": "Task has subtasks; schedule its pending subtasks instead",
            }],
            "decision_trace": {"mode": "targeted", "reason": "CONTAINER_TASK"},
        }

    consent = db.get(BehaviorConsent, uid)
    preferred = None
    if consent is not None and consent.enabled:
        signals = db.scalars(select(BehaviorEvent).where(
            BehaviorEvent.owner_uid == uid, BehaviorEvent.kind == "focus_completed"
        ).order_by(BehaviorEvent.happened_at.desc()).limit(90)).all()
        preferred = preferred_work_hour([(e.hour_of_day, e.duration_seconds) for e in signals])

    pref = db.get(Preference, uid)
    opts = (
        PlanningPreferences("Asia/Kolkata", time(8), time(22), 480, 10, preferred)
        if pref is None
        else PlanningPreferences(
            pref.timezone, pref.work_start, pref.work_end,
            pref.max_daily_minutes, pref.min_break_minutes, preferred,
        )
    )
    zone = ZoneInfo(opts.timezone)

    # Check prerequisites
    deps = db.scalars(select(TaskDependency).where(
        TaskDependency.owner_uid == uid, TaskDependency.task_id == task_id
    )).all()
    prereq_ids = {d.depends_on_id for d in deps}
    prereq_states = {
        t.id: t.status
        for t in db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(prereq_ids))).all()
    } if prereq_ids else {}
    unmet = sorted(pid for pid in prereq_ids if prereq_states.get(pid) != "completed")

    blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    events = db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()
    future_scheduled = 0
    occupied = []
    for blk in blocks:
        s, e = _aware(blk.starts_at), _aware(blk.ends_at)
        if blk.task_id == task_id and e > generated:
            future_scheduled += int((e - max(s, generated)).total_seconds() // 60)
        occupied.append(BusyInterval(s, e, counts_as_work=True))
    for ev in events:
        occupied.append(BusyInterval(_aware(ev.starts_at), _aware(ev.ends_at)))

    remaining = max(0, task.duration_minutes - future_scheduled)
    if unmet:
        reason = "Prerequisite tasks are not yet completed: " + ", ".join(unmet)
        return {
            "generated_at": generated.isoformat(),
            "timezone": opts.timezone,
            "changes_committed": False,
            "target_task_id": task_id,
            "blocks": [],
            "unscheduled": [{"task_id": task_id, "title": task.title, "remaining_minutes": remaining, "reason": reason}],
            "decision_trace": {"mode": "targeted", "reason": "PREREQUISITE_BLOCKED"},
        }
    if remaining <= 0:
        return {
            "generated_at": generated.isoformat(),
            "timezone": opts.timezone,
            "changes_committed": False,
            "target_task_id": task_id,
            "blocks": [],
            "unscheduled": [{"task_id": task_id, "title": task.title, "remaining_minutes": 0, "reason": "Task already has all remaining minutes scheduled"}],
            "decision_trace": {"mode": "targeted", "reason": "ALREADY_SCHEDULED"},
        }

    alloc_minutes = remaining if requested_minutes is None else min(requested_minutes, remaining)
    if requested_minutes is not None and exact_minutes and remaining < requested_minutes:
        return {
            "generated_at": generated.isoformat(),
            "timezone": opts.timezone,
            "changes_committed": False,
            "target_task_id": task_id,
            "blocks": [],
            "unscheduled": [{"task_id": task_id, "title": task.title, "remaining_minutes": remaining,
                             "reason": f"Only {remaining} minutes remain on '{task.title}', fewer than requested {requested_minutes} minutes"}],
            "decision_trace": {"mode": "targeted", "reason": "EXACT_MINUTES_UNMET"},
        }
    if not task.splittable and alloc_minutes < remaining:
        return {
            "generated_at": generated.isoformat(),
            "timezone": opts.timezone,
            "changes_committed": False,
            "target_task_id": task_id,
            "blocks": [],
            "unscheduled": [{"task_id": task_id, "title": task.title, "remaining_minutes": remaining,
                             "reason": f"Task '{task.title}' is indivisible ({remaining} min) and cannot be split into {alloc_minutes} min"}],
            "decision_trace": {"mode": "targeted", "reason": "INDIVISIBLE_TASK"},
        }

    w_start = _aware(window_start) or generated
    w_end = _aware(window_end)
    if w_start < generated:
        w_start = generated
    # Restrict search before w_start by marking [generated, w_start) as non-work busy if needed,
    # and cap horizon_days + deadline to w_end.
    effective_occupied = list(occupied)
    if w_start > generated:
        effective_occupied.append(BusyInterval(generated, w_start, counts_as_work=False))
    effective_deadline = _aware(task.deadline_at)
    if w_end is not None:
        effective_deadline = w_end if effective_deadline is None else min(effective_deadline, w_end)

    horizon_end = w_end or (generated + timedelta(days=7))
    days = max(1, min(14, (horizon_end.astimezone(zone).date() - generated.astimezone(zone).date()).days + 1))

    target_pt = PlanningTask(
        task.id,
        task.title,
        alloc_minutes,
        task.importance,
        effective_deadline,
        None,
        100,
        task.splittable,
    )
    suggestion, trace = choose_schedule([target_pt], effective_occupied, opts, generated, days)
    return {
        "generated_at": generated.isoformat(),
        "timezone": opts.timezone,
        "changes_committed": False,
        "target_task_id": task_id,
        "requested_minutes": alloc_minutes,
        "window_start": w_start.isoformat(),
        "window_end": w_end.isoformat() if w_end else None,
        "decision_trace": {**trace, "mode": "targeted"},
        "blocks": [
            {
                "task_id": b.task_id,
                "title": b.title,
                "starts_at": b.starts_at.astimezone(timezone.utc).isoformat(),
                "ends_at": b.ends_at.astimezone(timezone.utc).isoformat(),
                "duration_minutes": b.duration_minutes,
            }
            for b in suggestion.blocks
        ],
        "unscheduled": [
            {
                "task_id": u.task_id,
                "title": u.title,
                "remaining_minutes": u.remaining_minutes,
                "reason": u.reason,
            }
            for u in suggestion.unscheduled
        ],
    }


def _user_timezone_or_default(db: Session, uid: str) -> str:
    pref = db.get(Preference, uid)
    return pref.timezone if pref else "Asia/Kolkata"


@router.post("/preview-task")
def preview_single_task(
    body: TargetedPreviewRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return get_targeted_preview(
        db,
        user["uid"],
        body.task_id,
        requested_minutes=body.requested_minutes,
        window_start=body.window_start,
        window_end=body.window_end,
        exact_minutes=body.exact_minutes,
    )


class EventMoveReplanRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=36)
    new_starts_at: datetime
    new_ends_at: datetime
    horizon_days: int = Field(default=7, ge=1, le=14)


@router.post("/replan-event")
def preview_event_move_replan(
    body: EventMoveReplanRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    from .cross_replan import simulate_event_move_replan
    return simulate_event_move_replan(
        db,
        user["uid"],
        body.event_id,
        body.new_starts_at,
        body.new_ends_at,
        horizon_days=body.horizon_days,
    )


class ReplanTriggerRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=14)
    trigger: str = Field(default="user_request", max_length=60)
    create_proposal: bool = True
    notify: bool = True


def create_replan_proposal(
    db: Session,
    uid: str,
    days: int,
    trigger: str,
    create_proposal: bool = True,
    notify: bool = True,
) -> dict:
    """Build an adaptive replan proposal for one owner.

    Shared by the authenticated endpoint and the operator background worker so
    both paths apply identical validation, locking, and decision logging.
    """
    get_or_create_user(db, uid)
    db.scalar(select(User).where(User.uid == uid).with_for_update())

    user = {"uid": uid}
    preview = get_preview(days=days, user=user, db=db)
    if not preview["blocks"]:
        return {
            "proposal_id": None,
            "preview": preview,
            "trigger": trigger,
            "message": "No unblocked tasks fit this planning horizon. Keep current schedule.",
            "notification_sent": False,
        }

    if not create_proposal:
        return {
            "proposal_id": None,
            "preview": preview,
            "trigger": trigger,
            "message": "Preview generated without creating a proposal.",
            "notification_sent": False,
        }

    from .proposals_api import current_prefs
    ids = {row["task_id"] for row in preview["blocks"]}
    tasks = db.scalars(select(Task).where(Task.owner_uid == uid, Task.id.in_(ids))).all()
    versions = {task.id: task.version for task in tasks}

    plan = PlanProposal(
        owner_uid=uid,
        proposed_blocks=preview["blocks"],
        unscheduled=preview["unscheduled"],
        preferences_snapshot=current_prefs(db, uid),
        task_versions=versions,
        planning_trace=preview.get("decision_trace", {}),
        committed_block_ids=[],
    )
    db.add(plan)
    db.flush()

    db.add(PlanningDecisionLog(
        owner_uid=uid, proposal_id=plan.id, action="replanned",
        reason_codes=["ADAPTIVE_REPLAN", f"TRIGGER_{trigger.upper()}", "USER_REVIEW_REQUIRED"],
        before_blocks=[], after_blocks=preview["blocks"],
    ))

    notification_sent = False
    if notify:
        now_utc = datetime.now(timezone.utc)
        key = f"replan:{plan.id}:{int(now_utc.timestamp())}"
        clean_trigger = trigger.replace("_", " ")
        db.add(InAppNotification(
            owner_uid=uid, kind="replan_available", dedupe_key=key,
            message=f"Adaptive replan ready: {len(preview['blocks'])} sessions proposed ({clean_trigger}).",
            created_at=now_utc,
        ))
        notification_sent = True

    db.commit()
    db.refresh(plan)

    return {
        "proposal_id": plan.id,
        "preview": preview,
        "trigger": trigger,
        "message": f"Adaptive plan generated ({len(preview['blocks'])} sessions proposed). Review and approve in Approvals.",
        "notification_sent": notification_sent,
    }


@router.post("/replan")
def trigger_adaptive_replan(
    body: ReplanTriggerRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    return create_replan_proposal(
        db, user["uid"], body.days, body.trigger,
        create_proposal=body.create_proposal, notify=body.notify,
    )

