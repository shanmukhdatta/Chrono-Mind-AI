"""Read-only planning preview backed by PostgreSQL. Does not commit calendar changes."""
from collections import defaultdict
from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import (
    BehaviorConsent, BehaviorEvent, FixedEvent, Goal, InAppNotification,
    PlanProposal, PlanningDecisionLog, Preference, ScheduleBlock, Task, TaskDependency, User
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

